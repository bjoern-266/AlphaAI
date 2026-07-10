"""Registry der verfügbaren Paper-Trading-Modelle.

Die Registry ist die **einzige** Stelle, an der Paper-Trading-Modelle bekannt
gemacht werden. Neue Modelle werden ausschließlich hier registriert
(:meth:`PaperTradingRegistry.register` bzw. Ergänzung in
:func:`build_default_registry`). Die Engine kennt nur die Registry, nicht die
einzelnen Modellklassen (Open/Closed-Prinzip). Erbt von der generischen
:class:`core.registry.Registry`.
"""

from __future__ import annotations

from core.registry import Registry
from paper_trading.base import BasePaperTradingModel
from paper_trading.performance_model import PerformanceModel
from paper_trading.statistics_model import StatisticsModel


class PaperTradingRegistry(Registry[BasePaperTradingModel]):
    """Verwaltet die verfügbaren Paper-Trading-Modelle nach Name.

    Das öffentliche Interface (``register``/``get``/``__contains__``/``names``/
    ``len``) stammt aus der generischen Basis und bleibt unverändert.
    """

    def __init__(self) -> None:
        super().__init__(label="Paper-Trading-Modell")


def build_default_registry() -> PaperTradingRegistry:
    """Erzeugt eine Registry mit allen Standard-Paper-Trading-Modellen.

    Returns:
        Eine :class:`PaperTradingRegistry` mit Statistik- und Performance-Modell.
    """
    registry = PaperTradingRegistry()
    for model in (StatisticsModel(), PerformanceModel()):
        registry.register(model)
    return registry
