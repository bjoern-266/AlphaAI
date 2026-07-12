"""Lädt das Markt-Universum über eine injizierte Symbol-Quelle.

Der :class:`UniverseLoader` kennt die unterstützten Märkte (über ihre
:class:`~models.market_discovery.MarketDefinition`) und beschafft die Werte je
Markt ausschließlich über eine **injizierte** Quelle (``symbol_source``). Er
importiert **nichts** aus ``engines`` und **berechnet nichts** – er lädt und
vereinheitlicht ausschließlich Stammdaten.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

from market_discovery.market_universe import apply_definition, build_universe
from models.market_discovery import MarketDefinition, MarketSymbol, MarketUniverse


class DefinitionSource(Protocol):
    """Minimales Protokoll einer Markt-Definitions-Quelle (Registry-kompatibel)."""

    def __contains__(self, name: str) -> bool: ...  # noqa: D105

    def get(self, name: str) -> MarketDefinition: ...  # noqa: D102


# Signatur der injizierten Symbol-Quelle: Markt-Definition -> Werte des Marktes.
SymbolSource = Callable[[MarketDefinition], Sequence[MarketSymbol]]


def empty_symbol_source(definition: MarketDefinition) -> Sequence[MarketSymbol]:
    """Standard-Symbol-Quelle ohne Daten (echte Anbindung wird injiziert)."""
    return ()


class UniverseLoader:
    """Lädt ein :class:`MarketUniverse` aus registrierten Märkten.

    Args:
        definitions: Quelle der Markt-Definitionen (i. d. R. die Registry).
        symbol_source: Injizierte Quelle der Werte je Markt.
    """

    def __init__(
        self, definitions: DefinitionSource, symbol_source: SymbolSource = empty_symbol_source
    ) -> None:
        self._definitions = definitions
        self._symbol_source = symbol_source

    def load(self, markets: Sequence[str]) -> tuple[MarketUniverse, list[str]]:
        """Lädt alle Werte der angeforderten Märkte in ein Universum.

        Unbekannte Märkte werden mit einer Warnung übersprungen; Werte werden mit
        den Stammdaten ihres Marktes vervollständigt und global dedupliziert.
        """
        warnings: list[str] = []
        valid_markets: list[str] = []
        collected: list[MarketSymbol] = []
        for key in markets:
            if key not in self._definitions:
                warnings.append(f"Unbekannter Markt '{key}' übersprungen.")
                continue
            definition = self._definitions.get(key)
            valid_markets.append(key)
            for symbol in self._symbol_source(definition):
                collected.append(apply_definition(symbol, definition))
        universe, build_warnings = build_universe(collected, valid_markets)
        return universe, warnings + build_warnings
