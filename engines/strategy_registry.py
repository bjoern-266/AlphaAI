"""Registry der verfügbaren Strategien.

Die Registry ist die **einzige** Stelle, an der Strategien bekannt gemacht
werden. Neue Strategien werden ausschließlich hier registriert
(:meth:`StrategyRegistry.register` bzw. Ergänzung in
:func:`build_default_registry`). Die Engine kennt nur die Registry, nicht die
einzelnen Strategieklassen (Open/Closed-Prinzip).
"""

from __future__ import annotations

from core.registry import Registry
from strategies.base import BaseStrategy
from strategies.breakout_strategy import BreakoutStrategy
from strategies.fvg_strategy import FvgStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.momentum_strategy import MomentumStrategy
from strategies.trend_following import TrendFollowingStrategy


class StrategyRegistry(Registry[BaseStrategy]):
    """Verwaltet die verfügbaren Strategien nach Name.

    Erbt Registrierung/Abfrage von der generischen :class:`core.registry.Registry`;
    das öffentliche Interface bleibt unverändert.
    """

    def __init__(self) -> None:
        super().__init__(label="Strategie")


def build_default_registry() -> StrategyRegistry:
    """Erzeugt eine Registry mit allen Standard-Strategien.

    Returns:
        Eine :class:`StrategyRegistry` mit den fünf Standard-Strategien.
    """
    registry = StrategyRegistry()
    for strategy in (
        FvgStrategy(),
        TrendFollowingStrategy(),
        MomentumStrategy(),
        BreakoutStrategy(),
        MeanReversionStrategy(),
    ):
        registry.register(strategy)
    return registry
