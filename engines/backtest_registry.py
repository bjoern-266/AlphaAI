"""Registry der verfügbaren Backtest-Modelle.

Die Registry ist die **einzige** Stelle, an der Backtest-Modelle bekannt
gemacht werden. Neue Modelle werden ausschließlich hier registriert
(:meth:`BacktestRegistry.register` bzw. Ergänzung in
:func:`build_default_registry`). Die Engine kennt nur die Registry, nicht die
einzelnen Modellklassen (Open/Closed-Prinzip). Erbt von der generischen
:class:`core.registry.Registry`.
"""

from __future__ import annotations

from backtesting.base import BaseBacktestModel
from backtesting.benchmark_model import BenchmarkModel
from backtesting.drawdown_model import DrawdownModel
from backtesting.performance_model import PerformanceModel
from backtesting.ratio_model import RatioModel
from core.registry import Registry


class BacktestRegistry(Registry[BaseBacktestModel]):
    """Verwaltet die verfügbaren Backtest-Modelle nach Name.

    Das öffentliche Interface (``register``/``get``/``__contains__``/``names``/
    ``len``) stammt aus der generischen Basis und bleibt unverändert.
    """

    def __init__(self) -> None:
        super().__init__(label="Backtest-Modell")


def build_default_registry() -> BacktestRegistry:
    """Erzeugt eine Registry mit allen Standard-Backtest-Modellen.

    Returns:
        Eine :class:`BacktestRegistry` mit den vier Standard-Modellen
        (Performance, Drawdown, Ratio, Benchmark).
    """
    registry = BacktestRegistry()
    for model in (
        PerformanceModel(),
        DrawdownModel(),
        RatioModel(),
        BenchmarkModel(),
    ):
        registry.register(model)
    return registry
