"""Registry der verfügbaren Muster.

Die Registry ist die **einzige** Stelle, an der Muster bekannt gemacht werden.
Neue Muster werden ausschließlich hier registriert (:meth:`PatternRegistry.register`
bzw. Ergänzung in :func:`build_default_registry`). Die Engine kennt nur die
Registry, nicht die einzelnen Musterklassen (Open/Closed-Prinzip).
"""

from __future__ import annotations

from core.registry import Registry
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


class PatternRegistry(Registry[BasePattern]):
    """Verwaltet die verfügbaren Muster nach Name.

    Erbt Registrierung/Abfrage von der generischen :class:`core.registry.Registry`;
    das öffentliche Interface bleibt unverändert.
    """

    def __init__(self) -> None:
        super().__init__(label="Muster")


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
