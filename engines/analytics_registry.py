"""Registry der verfügbaren Analysemodelle.

Die Registry ist die **einzige** Stelle, an der Analysemodelle bekannt gemacht
werden. Neue Modelle werden ausschließlich hier registriert
(:meth:`AnalyticsRegistry.register` bzw. Ergänzung in
:func:`build_default_registry`). Die :class:`~engines.analytics_engine.AnalyticsEngine`
kennt nur die Registry, nicht die einzelnen Modellklassen, und muss für neue
Modelle **niemals** geändert werden (Open/Closed-Prinzip). Erbt von der
generischen :class:`core.registry.Registry`.
"""

from __future__ import annotations

from analytics.base import BaseAnalyticsModel
from analytics.journal_analysis import JournalAnalysisModel
from analytics.market_analysis import MarketAnalysisModel
from analytics.pattern_analysis import PatternAnalysisModel
from analytics.performance_analyzer import PerformanceAnalyzer
from analytics.recommendation_analysis import RecommendationAnalysisModel
from analytics.risk_analysis import RiskAnalysisModel
from analytics.strategy_analysis import StrategyAnalysisModel
from analytics.summary_analysis import SummaryAnalysisModel
from analytics.time_analysis import TimeAnalysisModel
from analytics.trade_statistics import TradeStatisticsModel
from core.registry import Registry


class AnalyticsRegistry(Registry[BaseAnalyticsModel]):
    """Verwaltet die verfügbaren Analysemodelle nach Name.

    Das öffentliche Interface (``register``/``get``/``__contains__``/``names``/
    ``len``) stammt aus der generischen Basis und bleibt unverändert.
    """

    def __init__(self) -> None:
        super().__init__(label="Analysemodell")


def build_default_registry() -> AnalyticsRegistry:
    """Erzeugt eine Registry mit allen zehn Standard-Analysemodellen."""
    registry = AnalyticsRegistry()
    for model in (
        TradeStatisticsModel(),
        PerformanceAnalyzer(),
        PatternAnalysisModel(),
        StrategyAnalysisModel(),
        RecommendationAnalysisModel(),
        RiskAnalysisModel(),
        MarketAnalysisModel(),
        TimeAnalysisModel(),
        JournalAnalysisModel(),
        SummaryAnalysisModel(),
    ):
        registry.register(model)
    return registry
