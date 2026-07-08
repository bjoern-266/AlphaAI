"""Registry der verfügbaren Muster.

Die Registry ist die **einzige** Stelle, an der Muster bekannt gemacht werden.
Neue Muster werden ausschließlich hier registriert (:meth:`PatternRegistry.register`
bzw. Ergänzung in :func:`build_default_registry`). Die Engine kennt nur die
Registry, nicht die einzelnen Musterklassen (Open/Closed-Prinzip).
"""

from __future__ import annotations

from patterns.base import BasePattern
from patterns.bos import BosPattern
from patterns.breaker_block import BreakerBlockPattern
from patterns.choch import ChochPattern
from patterns.equal_highs import EqualHighsPattern
from patterns.equal_lows import EqualLowsPattern
from patterns.fvg import FvgPattern
from patterns.liquidity_sweep import LiquiditySweepPattern
from patterns.market_structure import MarketStructurePattern
from patterns.mitigation_block import MitigationBlockPattern
from patterns.order_block import OrderBlockPattern
from patterns.trend_structure import TrendStructurePattern


class PatternRegistry:
    """Verwaltet die verfügbaren Muster nach Name."""

    def __init__(self) -> None:
        self._by_name: dict[str, BasePattern] = {}

    def register(self, pattern: BasePattern) -> None:
        """Registriert ein Muster.

        Raises:
            ValueError: Wenn bereits ein Muster mit demselben Namen existiert.
        """
        if pattern.name in self._by_name:
            raise ValueError(f"Muster '{pattern.name}' ist bereits registriert.")
        self._by_name[pattern.name] = pattern

    def get(self, name: str) -> BasePattern:
        """Gibt das Muster mit dem Namen zurück.

        Raises:
            KeyError: Wenn kein Muster mit diesem Namen registriert ist.
        """
        if name not in self._by_name:
            raise KeyError(f"Unbekanntes Muster '{name}'.")
        return self._by_name[name]

    def __contains__(self, name: str) -> bool:
        """Prüft, ob ein Mustername registriert ist."""
        return name in self._by_name

    def names(self) -> list[str]:
        """Gibt die registrierten Musternamen sortiert zurück."""
        return sorted(self._by_name)

    def __len__(self) -> int:
        """Anzahl registrierter Muster."""
        return len(self._by_name)


def build_default_registry() -> PatternRegistry:
    """Erzeugt eine Registry mit allen Standard-Mustern.

    Returns:
        Eine :class:`PatternRegistry` mit den elf Standard-Mustern (acht
        implementiert, drei vorbereitet).
    """
    registry = PatternRegistry()
    for pattern in (
        FvgPattern(),
        BosPattern(),
        ChochPattern(),
        EqualHighsPattern(),
        EqualLowsPattern(),
        LiquiditySweepPattern(),
        MarketStructurePattern(),
        TrendStructurePattern(),
        OrderBlockPattern(),
        BreakerBlockPattern(),
        MitigationBlockPattern(),
    ):
        registry.register(pattern)
    return registry
