"""Aufbau und Pflege eines :class:`~models.market_discovery.MarketUniverse`.

Reine Struktur-Operationen (Zusammenführen, Deduplizieren, Vervollständigen der
Stammdaten). Es findet **keine** Berechnung von Kennzahlen statt.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import replace

from models.market_discovery import MarketDefinition, MarketSymbol, MarketUniverse


def apply_definition(symbol: MarketSymbol, definition: MarketDefinition) -> MarketSymbol:
    """Ergänzt fehlende Stammdaten eines Werts aus der Markt-Definition."""
    return replace(
        symbol,
        market=symbol.market or definition.name,
        country=symbol.country or definition.country,
        exchange=symbol.exchange or definition.exchange,
    )


def build_universe(
    symbols: Iterable[MarketSymbol], markets: Sequence[str], name: str = "universe"
) -> tuple[MarketUniverse, list[str]]:
    """Baut ein Universum aus Werten, dedupliziert nach Ticker.

    Returns:
        Das Universum sowie eine Liste mit Warnungen (ungültige/doppelte Werte).
    """
    seen: set[str] = set()
    kept: list[MarketSymbol] = []
    warnings: list[str] = []
    for symbol in symbols:
        if not symbol.ticker:
            warnings.append("Wert ohne Ticker übersprungen.")
            continue
        if symbol.ticker in seen:
            warnings.append(f"Doppelter Kandidat '{symbol.ticker}' übersprungen.")
            continue
        seen.add(symbol.ticker)
        kept.append(symbol)
    return MarketUniverse(name=name, symbols=tuple(kept), markets=tuple(markets)), warnings
