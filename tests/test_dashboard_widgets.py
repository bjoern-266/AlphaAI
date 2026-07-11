"""Tests der Widgets (bauen Anzeige-Beschreibungen, berechnen nichts)."""

from __future__ import annotations

from dashboard.settings import DashboardSettings
from dashboard.state import DashboardState
from dashboard.theme import load_theme
from dashboard.viewmodels import ReportBundle, build_view_model
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
from dashboard.widgets.base import WidgetContext
from dashboard.widgets.journal import JournalTableWidget
from dashboard.widgets.live import ReasonsWidget, WatchlistWidget
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
from engines.indicator_result import IndicatorResult
from models.dashboard import (
    KIND_CARDS,
    KIND_CHART,
    KIND_STATUS,
    KIND_TABLE,
    WidgetSpec,
)
from tests.dashboard_helpers import (
    make_analytics_report,
    make_backtest_report,
    make_paper_report,
    make_recommendation_report,
)

THEME = load_theme()
SETTINGS = DashboardSettings()


def _context(bundle: ReportBundle, state: DashboardState | None = None) -> WidgetContext:
    return WidgetContext(
        view_model=build_view_model(bundle),
        theme=THEME,
        settings=SETTINGS,
        state=state or DashboardState(),
    )


def _full_bundle() -> ReportBundle:
    return ReportBundle(
        recommendation=make_recommendation_report(),
        paper_trading=make_paper_report(),
        backtest=make_backtest_report(),
        analytics=make_analytics_report(),
        indicator=IndicatorResult(outputs={}, valid=True, metadata={}),
    )


# --------------------------------------------------------------------------- #
# Overview                                                                    #
# --------------------------------------------------------------------------- #


def test_overview_kpis_populated():
    spec = OverviewKpisWidget().build(_context(_full_bundle()))
    assert spec.kind == KIND_CARDS
    assert spec.placeholder is False
    assert len(spec.cards) == 9


def test_overview_kpis_placeholder_when_empty():
    spec = OverviewKpisWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_system_status_widget():
    spec = SystemStatusWidget().build(_context(_full_bundle()))
    assert spec.kind == KIND_STATUS
    assert len(spec.status_items) == 5


def test_recommendation_feed_populated():
    spec = RecommendationFeedWidget().build(_context(_full_bundle()))
    assert spec.placeholder is False
    assert len(spec.items) == 2


def test_recommendation_feed_placeholder():
    spec = RecommendationFeedWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


# --------------------------------------------------------------------------- #
# Live Analysis                                                               #
# --------------------------------------------------------------------------- #


def test_watchlist_table():
    spec = WatchlistWidget().build(_context(_full_bundle()))
    assert spec.kind == KIND_TABLE
    assert spec.table is not None
    assert len(spec.table.rows) == 2
    assert spec.table.columns[0] == "Symbol"


def test_watchlist_placeholder_when_empty():
    spec = WatchlistWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_reasons_widget_shows_first_row():
    spec = ReasonsWidget().build(_context(_full_bundle()))
    assert spec.placeholder is False
    assert any("Trend intakt" in item for item in spec.items)


def test_reasons_widget_placeholder_when_empty():
    spec = ReasonsWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


# --------------------------------------------------------------------------- #
# Portfolio                                                                   #
# --------------------------------------------------------------------------- #


def test_portfolio_kpis():
    spec = PortfolioKpisWidget().build(_context(_full_bundle()))
    assert spec.kind == KIND_CARDS
    assert spec.placeholder is False
    assert len(spec.cards) == 9


def test_portfolio_kpis_placeholder():
    spec = PortfolioKpisWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_portfolio_equity_chart():
    spec = PortfolioEquityWidget().build(_context(_full_bundle()))
    assert spec.kind == KIND_CHART
    assert spec.chart is not None
    assert spec.chart.chart_type == "area"
    assert spec.placeholder is False


def test_portfolio_equity_placeholder_when_empty():
    spec = PortfolioEquityWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


# --------------------------------------------------------------------------- #
# Backtesting                                                                 #
# --------------------------------------------------------------------------- #


def test_backtest_kpis():
    spec = BacktestKpisWidget().build(_context(_full_bundle()))
    assert spec.placeholder is False
    assert len(spec.cards) == 5


def test_backtest_kpis_placeholder():
    spec = BacktestKpisWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_backtest_equity_chart_is_line():
    spec = BacktestEquityWidget().build(_context(_full_bundle()))
    assert spec.chart is not None
    assert spec.chart.chart_type == "line"


def test_trade_list():
    spec = TradeListWidget().build(_context(_full_bundle()))
    assert spec.table is not None
    assert len(spec.table.rows) == 3


def test_trade_list_placeholder():
    spec = TradeListWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


# --------------------------------------------------------------------------- #
# Analytics                                                                   #
# --------------------------------------------------------------------------- #


def test_long_short_donut():
    spec = LongShortWidget().build(_context(_full_bundle()))
    assert spec.chart is not None
    assert spec.chart.chart_type == "donut"
    assert spec.placeholder is False


def test_long_short_placeholder_when_empty():
    spec = LongShortWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_strategy_perf_table():
    spec = StrategyPerfWidget().build(_context(_full_bundle()))
    assert spec.table is not None
    assert spec.table.columns[0] == "Gruppe"
    assert not spec.table.is_empty


def test_pattern_perf_table():
    spec = PatternPerfWidget().build(_context(_full_bundle()))
    assert not spec.placeholder


def test_risk_perf_table():
    spec = RiskPerfWidget().build(_context(_full_bundle()))
    assert not spec.placeholder


def test_recommendation_perf_table():
    spec = RecommendationPerfWidget().build(_context(_full_bundle()))
    assert not spec.placeholder


def test_market_phase_table():
    spec = MarketPhaseWidget().build(_context(_full_bundle()))
    assert not spec.placeholder


def test_group_table_placeholder_when_empty():
    spec = StrategyPerfWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_time_analysis_weekday():
    spec = TimeAnalysisWidget().build(_context(_full_bundle()))
    assert spec.table is not None
    assert not spec.table.is_empty


def test_journal_analysis_cards():
    spec = JournalAnalysisWidget().build(_context(_full_bundle()))
    assert spec.kind == KIND_CARDS
    assert len(spec.cards) == 5
    assert spec.placeholder is False


def test_journal_analysis_placeholder():
    spec = JournalAnalysisWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


# --------------------------------------------------------------------------- #
# Performance                                                                 #
# --------------------------------------------------------------------------- #


def test_performance_equity():
    spec = PerformanceEquityWidget().build(_context(_full_bundle()))
    assert spec.chart is not None
    assert not spec.placeholder


def test_drawdown_widget():
    spec = DrawdownWidget().build(_context(_full_bundle()))
    assert spec.chart is not None
    assert not spec.placeholder


def test_profit_distribution():
    spec = ProfitDistributionWidget().build(_context(_full_bundle()))
    assert spec.chart is not None
    assert spec.chart.chart_type == "bar"


def test_holding_time():
    spec = HoldingTimeWidget().build(_context(_full_bundle()))
    assert spec.chart is not None
    assert not spec.placeholder


def test_returns_widget_always_placeholder():
    # Perioden-Renditen sind in keinem Report -> immer Platzhalter (keine Berechnung).
    spec = ReturnsWidget().build(_context(_full_bundle()))
    assert spec.placeholder is True
    assert len(spec.cards) == 3


# --------------------------------------------------------------------------- #
# Journal (Suche/Filter/Sortierung)                                           #
# --------------------------------------------------------------------------- #


def test_journal_table_all_rows():
    spec = JournalTableWidget().build(_context(_full_bundle()))
    assert spec.table is not None
    assert len(spec.table.rows) == 2
    assert spec.metadata["total"] == 2


def test_journal_table_search_filters_rows():
    state = DashboardState()
    state.set_search("Take-Profit")
    spec = JournalTableWidget().build(_context(_full_bundle(), state))
    assert spec.metadata["shown"] <= spec.metadata["total"]


def test_journal_table_search_no_match():
    state = DashboardState()
    state.set_search("zzzz-nichts")
    spec = JournalTableWidget().build(_context(_full_bundle(), state))
    assert spec.placeholder is True


def test_journal_table_direction_filter():
    state = DashboardState()
    state.set_filter("journal_direction", "short")
    spec = JournalTableWidget().build(_context(_full_bundle(), state))
    # Alle Fixtures sind LONG -> Short-Filter leert die Tabelle.
    assert spec.placeholder is True


def test_journal_table_sort_by_pnl():
    state = DashboardState()
    state.set_sort("journal", "pnl", ascending=False)
    spec = JournalTableWidget().build(_context(_full_bundle(), state))
    assert spec.table is not None


# --------------------------------------------------------------------------- #
# Recommendations & Settings                                                  #
# --------------------------------------------------------------------------- #


def test_recommendations_table():
    spec = RecommendationsTableWidget().build(_context(_full_bundle()))
    assert spec.table is not None
    assert len(spec.table.rows) == 2


def test_recommendations_placeholder():
    spec = RecommendationsTableWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_settings_widget_display_only():
    spec = SettingsWidget().build(_context(ReportBundle()))
    assert spec.kind == KIND_CARDS
    labels = {c.label for c in spec.cards}
    assert "Dark Mode" in labels
    assert "Refresh Rate" in labels
    # Keine Handelsparameter.
    assert "Risk" not in labels
    assert "Capital" not in labels


def test_every_widget_returns_widget_spec():
    ctx = _context(_full_bundle())
    widgets = [
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
        SettingsWidget(),
    ]
    for widget in widgets:
        spec = widget.build(ctx)
        assert isinstance(spec, WidgetSpec)
        assert spec.widget_id == widget.name
