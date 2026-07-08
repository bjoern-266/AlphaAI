"""Anfrageobjekt für Marktdaten.

Ein :class:`MarketRequest` beschreibt vollständig und unveränderlich, welche
Daten angefordert werden. Es ist bewusst provider-unabhängig: Der konkrete
Provider entscheidet, ob er die gewünschten Werte unterstützt.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.exceptions import AlphaAIError


class InvalidRequestError(AlphaAIError):
    """Wird ausgelöst, wenn ein :class:`MarketRequest` unzulässig ist."""


@dataclass(frozen=True, slots=True)
class MarketRequest:
    """Beschreibt eine Marktdatenanfrage.

    Attributes:
        symbols: Zu ladende Symbole (yfinance-Notation). Werden normalisiert
            (getrimmt, Großschreibung) und als Tupel gespeichert.
        timeframe: Zeitraum/Rückschau der Historie (z. B. ``"6mo"``, ``"1y"``).
        interval: Kerzenintervall (z. B. ``"1d"``, ``"1h"``, ``"5m"``).
        market: Bezeichnung des Marktes/Universums (z. B. ``"USA"``, ``"DAX"``).
        use_cache: Ob für diese Anfrage der Cache verwendet werden darf.
    """

    symbols: tuple[str, ...]
    timeframe: str
    interval: str
    market: str = "default"
    use_cache: bool = True

    def __post_init__(self) -> None:
        """Normalisiert und validiert die Felder nach der Initialisierung."""
        normalized = tuple(
            symbol.strip().upper() for symbol in self.symbols if symbol and symbol.strip()
        )
        # ``frozen`` erlaubt kein direktes Setzen – Umweg über object.__setattr__.
        object.__setattr__(self, "symbols", normalized)
        object.__setattr__(self, "timeframe", self.timeframe.strip())
        object.__setattr__(self, "interval", self.interval.strip())
        object.__setattr__(self, "market", self.market.strip() or "default")

        if not normalized:
            raise InvalidRequestError("MarketRequest benötigt mindestens ein Symbol.")
        if not self.timeframe:
            raise InvalidRequestError("MarketRequest benötigt einen Zeitraum (timeframe).")
        if not self.interval:
            raise InvalidRequestError("MarketRequest benötigt ein Intervall (interval).")

    @property
    def is_intraday(self) -> bool:
        """Gibt zurück, ob es sich um ein Intraday-Intervall handelt.

        Intraday-Intervalle enden auf Minuten (``m``) oder Stunden (``h``);
        Tages-/Wochen-/Monatsintervalle (z. B. ``1d``, ``1wk``, ``1mo``) nicht.
        """
        return self.interval[-1:].lower() in {"m", "h"}

    def cache_key(self) -> str:
        """Erzeugt einen stabilen Cache-Schlüssel für diese Anfrage.

        Die Reihenfolge der Symbole ist für den Schlüssel unerheblich, damit
        gleiche Anfragen unabhängig von der Eingabereihenfolge denselben
        Schlüssel erhalten.
        """
        symbol_part = ",".join(sorted(self.symbols))
        return f"{self.market}|{symbol_part}|{self.timeframe}|{self.interval}"


def build_request(
    symbols: list[str] | tuple[str, ...],
    timeframe: str,
    interval: str,
    market: str = "default",
    use_cache: bool = True,
) -> MarketRequest:
    """Bequemer Konstruktor für :class:`MarketRequest` aus einer Symbolliste.

    Args:
        symbols: Liste oder Tupel der Symbole.
        timeframe: Zeitraum/Rückschau.
        interval: Kerzenintervall.
        market: Markt-/Universumsbezeichnung.
        use_cache: Ob der Cache verwendet werden darf.

    Returns:
        Ein validiertes :class:`MarketRequest`.
    """
    return MarketRequest(
        symbols=tuple(symbols),
        timeframe=timeframe,
        interval=interval,
        market=market,
        use_cache=use_cache,
    )
