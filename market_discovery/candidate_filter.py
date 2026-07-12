"""Vorfilter für Kandidaten (vor der vollständigen Analyse).

Entfernt ungeeignete Werte anhand **vorhandener** Stammdaten (Liquidität,
Volumen, Historie, gültige Kurse, Handelbarkeit, Delisting, Penny Stocks). Alle
Grenzwerte stammen ausschließlich aus ``market_discovery_rules.toml``. Es findet
**keine** Berechnung von Kennzahlen statt.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from models.market_discovery import MarketSymbol, RejectedCandidate


@dataclass(frozen=True, slots=True)
class CandidateFilter:
    """Grenzwerte des Vorfilters (unveränderlich, aus der Regeldatei).

    ``None`` bei einer Grenze bedeutet: dieses Kriterium schränkt nicht ein.

    Attributes:
        min_price: Mindestkurs oder ``None``.
        min_volume: Mindest-Handelsvolumen (Stück) oder ``None``.
        min_dollar_volume: Mindest-Liquidität (Umsatz) oder ``None``.
        min_history_days: Mindest-Kurshistorie in Tagen oder ``None``.
        require_tradable: Ob nur handelbare Werte zugelassen werden.
        exclude_delisted: Ob delistete Werte ausgeschlossen werden.
        exclude_penny: Ob Penny Stocks ausgeschlossen werden.
        penny_price: Kursgrenze, ab der ein Wert **nicht** mehr als Penny gilt.
    """

    min_price: float | None = None
    min_volume: float | None = None
    min_dollar_volume: float | None = None
    min_history_days: int | None = None
    require_tradable: bool = True
    exclude_delisted: bool = True
    exclude_penny: bool = False
    penny_price: float = 1.0

    def reason(self, symbol: MarketSymbol) -> str | None:
        """Gibt den Ablehnungsgrund eines Werts zurück (``None`` = behalten)."""
        if self.require_tradable and not symbol.tradable:
            return "nicht handelbar"
        if self.exclude_delisted and symbol.delisted:
            return "delisted"
        if symbol.price is None:
            return "kein gültiger Kurs"
        if symbol.price <= 0:
            return "ungültiger Kurs"
        if self.exclude_penny and symbol.price < self.penny_price:
            return "Penny Stock"
        if self.min_price is not None and symbol.price < self.min_price:
            return "Kurs unter Mindestwert"
        if self.min_volume is not None and (
            symbol.volume is None or symbol.volume < self.min_volume
        ):
            return "Volumen zu gering"
        if self.min_dollar_volume is not None and (
            symbol.average_dollar_volume is None
            or symbol.average_dollar_volume < self.min_dollar_volume
        ):
            return "Liquidität zu gering"
        if self.min_history_days is not None and (
            symbol.history_days is None or symbol.history_days < self.min_history_days
        ):
            return "Historie zu kurz"
        return None


def load_candidate_filter(config: Mapping[str, Any]) -> CandidateFilter:
    """Baut den Vorfilter aus der Regel-Konfiguration (nur Anzeige/Auswahl)."""

    def _opt(key: str) -> float | None:
        value = config.get(key)
        return (
            float(value)
            if isinstance(value, (int, float)) and not isinstance(value, bool)
            else None
        )

    history = config.get("min_history_days")
    return CandidateFilter(
        min_price=_opt("min_price"),
        min_volume=_opt("min_volume"),
        min_dollar_volume=_opt("min_dollar_volume"),
        min_history_days=(
            int(history) if isinstance(history, int) and not isinstance(history, bool) else None
        ),
        require_tradable=bool(config.get("require_tradable", True)),
        exclude_delisted=bool(config.get("exclude_delisted", True)),
        exclude_penny=bool(config.get("exclude_penny", False)),
        penny_price=float(config.get("penny_price", 1.0)),
    )


def apply_filter(
    symbols: Sequence[MarketSymbol], candidate_filter: CandidateFilter
) -> tuple[tuple[MarketSymbol, ...], tuple[RejectedCandidate, ...]]:
    """Teilt die Werte in behaltene und (mit Grund) verworfene Kandidaten."""
    kept: list[MarketSymbol] = []
    rejected: list[RejectedCandidate] = []
    for symbol in symbols:
        reason = candidate_filter.reason(symbol)
        if reason is None:
            kept.append(symbol)
        else:
            rejected.append(RejectedCandidate(ticker=symbol.ticker, reason=reason))
    return tuple(kept), tuple(rejected)
