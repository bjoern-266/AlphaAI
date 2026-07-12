"""Registry der verfügbaren Widgets.

Die Registry ist die **einzige** Stelle, an der Widgets bekannt gemacht werden.
Neue Widgets werden ausschließlich hier registriert; die
:class:`~dashboard.engine.DashboardEngine` kennt nur die Registry, nicht die
einzelnen Widget-Klassen (Open/Closed-Prinzip) und bleibt unverändert. Erbt von
der generischen :class:`core.registry.Registry`.
"""

from __future__ import annotations

from core.registry import Registry
from dashboard.widgets.analytics import (
    JournalAnalysisWidget,
    LongShortWidget,
    MarketPhaseWidget,
    PatternPerfWidget,
    RecommendationPerfWidget,
    RiskPerfWidget,
    StrategyPerfWidget,
    TimeAnalysisWidget,
)
from dashboard.widgets.backtest import (
    BacktestEquityWidget,
    BacktestKpisWidget,
    TradeListWidget,
)
from dashboard.widgets.base import BaseWidget
from dashboard.widgets.journal import JournalTableWidget
from dashboard.widgets.live import ReasonsWidget, WatchlistWidget
from dashboard.widgets.market_intelligence import (
    MarketIntelligenceStatsWidget,
    OpportunityExplanationWidget,
    OpportunityHeatmapWidget,
    OpportunityRankingWidget,
    TopOpportunitiesWidget,
)
from dashboard.widgets.overview import (
    OverviewKpisWidget,
    RecommendationFeedWidget,
    SystemStatusWidget,
)
from dashboard.widgets.performance import (
    DrawdownWidget,
    HoldingTimeWidget,
    PerformanceEquityWidget,
    ProfitDistributionWidget,
    ReturnsWidget,
)
from dashboard.widgets.portfolio import PortfolioEquityWidget, PortfolioKpisWidget
from dashboard.widgets.recommendations import RecommendationsTableWidget
from dashboard.widgets.settings import SettingsWidget


class WidgetRegistry(Registry[BaseWidget]):
    """Verwaltet die verfügbaren Widgets nach Name.

    Das öffentliche Interface (``register``/``get``/``__contains__``/``names``/
    ``len``) stammt aus der generischen Basis und bleibt unverändert.
    """

    def __init__(self) -> None:
        super().__init__(label="Widget")


# Alle Standard-Widgets (die einzige Stelle, an der neue Widgets ergänzt werden).
_DEFAULT_WIDGETS: tuple[BaseWidget, ...] = (
    OverviewKpisWidget(),
    SystemStatusWidget(),
    RecommendationFeedWidget(),
    WatchlistWidget(),
    ReasonsWidget(),
    PortfolioKpisWidget(),
    PortfolioEquityWidget(),
    BacktestKpisWidget(),
    BacktestEquityWidget(),
    TradeListWidget(),
    LongShortWidget(),
    StrategyPerfWidget(),
    PatternPerfWidget(),
    RiskPerfWidget(),
    RecommendationPerfWidget(),
    MarketPhaseWidget(),
    TimeAnalysisWidget(),
    JournalAnalysisWidget(),
    PerformanceEquityWidget(),
    DrawdownWidget(),
    ProfitDistributionWidget(),
    HoldingTimeWidget(),
    ReturnsWidget(),
    JournalTableWidget(),
    RecommendationsTableWidget(),
    TopOpportunitiesWidget(),
    OpportunityRankingWidget(),
    OpportunityHeatmapWidget(),
    OpportunityExplanationWidget(),
    MarketIntelligenceStatsWidget(),
    SettingsWidget(),
)


def build_default_registry() -> WidgetRegistry:
    """Erzeugt eine Registry mit allen Standard-Widgets."""
    registry = WidgetRegistry()
    for widget in _DEFAULT_WIDGETS:
        registry.register(widget)
    return registry
