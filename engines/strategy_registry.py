"""Registry der verfügbaren Strategien.

Die Registry ist die **einzige** Stelle, an der Strategien bekannt gemacht
werden. Neue Strategien werden ausschließlich hier registriert
(:meth:`StrategyRegistry.register` bzw. Ergänzung in
:func:`build_default_registry`). Die Engine kennt nur die Registry, nicht die
einzelnen Strategieklassen (Open/Closed-Prinzip).
"""

from __future__ import annotations

from strategies.base import BaseStrategy
from strategies.breakout_strategy import BreakoutStrategy
from strategies.fvg_strategy import FvgStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.momentum_strategy import MomentumStrategy
from strategies.trend_following import TrendFollowingStrategy


class StrategyRegistry:
    """Verwaltet die verfügbaren Strategien nach Name."""

    def __init__(self) -> None:
        self._by_name: dict[str, BaseStrategy] = {}

    def register(self, strategy: BaseStrategy) -> None:
        """Registriert eine Strategie.

        Raises:
            ValueError: Wenn bereits eine Strategie mit demselben Namen existiert.
        """
        if strategy.name in self._by_name:
            raise ValueError(f"Strategie '{strategy.name}' ist bereits registriert.")
        self._by_name[strategy.name] = strategy

    def get(self, name: str) -> BaseStrategy:
        """Gibt die Strategie mit dem Namen zurück.

        Raises:
            KeyError: Wenn keine Strategie mit diesem Namen registriert ist.
        """
        if name not in self._by_name:
            raise KeyError(f"Unbekannte Strategie '{name}'.")
        return self._by_name[name]

    def __contains__(self, name: str) -> bool:
        """Prüft, ob ein Strategiename registriert ist."""
        return name in self._by_name

    def names(self) -> list[str]:
        """Gibt die registrierten Strategienamen sortiert zurück."""
        return sorted(self._by_name)

    def __len__(self) -> int:
        """Anzahl registrierter Strategien."""
        return len(self._by_name)


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
