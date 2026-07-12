"""Tests der Market-Intelligence-Dashboardseite (nur Anzeige des Reports)."""

from __future__ import annotations

from dashboard.engine import DashboardEngine
from dashboard.settings import DashboardSettings
from dashboard.state import DashboardState, Page
from dashboard.theme import load_theme
from dashboard.viewmodels import MarketIntelligenceVM, ReportBundle, build_view_model
from dashboard.widgets.base import WidgetContext
from dashboard.widgets.market_intelligence import (
    MarketIntelligenceStatsWidget,
    OpportunityExplanationWidget,
    OpportunityHeatmapWidget,
    OpportunityRankingWidget,
    TopOpportunitiesWidget,
)
from engines.market_intelligence_engine import MarketIntelligenceEngine
from models.dashboard import KIND_CARDS, KIND_CHART, KIND_LIST, KIND_TABLE
from models.recommendation import Direction
from tests.market_intelligence_helpers import make_full_candidate

THEME = load_theme()
SETTINGS = DashboardSettings()


def _report():
    candidates = [
        make_full_candidate("HIGH", rating=95.0, risk_factor=90.0, direction=Direction.LONG),
        make_full_candidate("MID", rating=60.0, risk_factor=50.0, direction=Direction.SHORT),
    ]
    return MarketIntelligenceEngine.from_config().analyze(candidates)


def _bundle():
    return ReportBundle(opportunity=_report())


def _context(bundle: ReportBundle, state: DashboardState | None = None) -> WidgetContext:
    return WidgetContext(
        view_model=build_view_model(bundle),
        theme=THEME,
        settings=SETTINGS,
        state=state or DashboardState(),
    )


# --- View Model ------------------------------------------------------------ #


def test_vm_empty_without_report():
    vm = build_view_model(ReportBundle()).market_intelligence
    assert isinstance(vm, MarketIntelligenceVM)
    assert vm.rows == ()
    assert vm.analyzed_count is None


def test_vm_reads_rows():
    vm = build_view_model(_bundle()).market_intelligence
    assert len(vm.rows) == 2
    assert vm.rows[0].ticker == "HIGH"
    assert vm.rows[0].rank == 1


def test_vm_reads_statistics():
    vm = build_view_model(_bundle()).market_intelligence
    assert vm.analyzed_count == 2
    assert vm.long_count == 1
    assert vm.short_count == 1
    assert vm.average_score is not None


def test_vm_reads_explanations():
    vm = build_view_model(_bundle()).market_intelligence
    assert len(vm.explanations) == 2
    assert vm.explanations[0].ticker == "HIGH"


def test_vm_heatmap_data():
    vm = build_view_model(_bundle()).market_intelligence
    assert vm.heatmap_labels == ("HIGH", "MID")
    assert len(vm.heatmap_scores) == 2


def test_vm_watchlists():
    vm = build_view_model(_bundle()).market_intelligence
    assert vm.watchlist_top == ("HIGH", "MID")
    assert vm.watchlist_long == ("HIGH",)
    assert vm.watchlist_short == ("MID",)


# --- Widgets --------------------------------------------------------------- #


def test_top_opportunities_table():
    spec = TopOpportunitiesWidget().build(_context(_bundle()))
    assert spec.kind == KIND_TABLE
    assert spec.table is not None
    assert len(spec.table.rows) == 2
    assert not spec.placeholder


def test_top_opportunities_placeholder_when_empty():
    spec = TopOpportunitiesWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_ranking_table():
    spec = OpportunityRankingWidget().build(_context(_bundle()))
    assert spec.kind == KIND_TABLE
    assert spec.metadata["total"] == 2


def test_ranking_search_filters():
    state = DashboardState()
    state.set_search("HIGH")
    spec = OpportunityRankingWidget().build(_context(_bundle(), state))
    assert spec.metadata["shown"] == 1


def test_ranking_search_no_match():
    state = DashboardState()
    state.set_search("zzz")
    spec = OpportunityRankingWidget().build(_context(_bundle(), state))
    assert spec.placeholder is True


def test_ranking_direction_filter():
    state = DashboardState()
    state.set_filter("opportunity_direction", "short")
    spec = OpportunityRankingWidget().build(_context(_bundle(), state))
    assert spec.metadata["shown"] == 1


def test_heatmap_chart():
    spec = OpportunityHeatmapWidget().build(_context(_bundle()))
    assert spec.kind == KIND_CHART
    assert spec.chart is not None
    assert spec.chart.chart_type == "bar"
    assert not spec.placeholder


def test_heatmap_placeholder_when_empty():
    spec = OpportunityHeatmapWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_explanation_list():
    spec = OpportunityExplanationWidget().build(_context(_bundle()))
    assert spec.kind == KIND_LIST
    assert spec.items
    assert not spec.placeholder


def test_explanation_placeholder_when_empty():
    spec = OpportunityExplanationWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_statistics_cards():
    spec = MarketIntelligenceStatsWidget().build(_context(_bundle()))
    assert spec.kind == KIND_CARDS
    assert len(spec.cards) == 7
    assert not spec.placeholder


def test_statistics_placeholder_when_empty():
    spec = MarketIntelligenceStatsWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


# --- Page über die Engine -------------------------------------------------- #


def test_engine_builds_market_intelligence_page():
    engine = DashboardEngine.from_config()
    view = engine.build_view(DashboardState(active_page=Page.MARKET_INTELLIGENCE), _bundle())
    assert view.page == "market_intelligence"
    assert view.valid is True
    assert set(view.widgets) == {
        "mi_top_opportunities",
        "mi_ranking",
        "mi_heatmap",
        "mi_statistics",
        "mi_explanation",
    }


def test_page_valid_with_empty_bundle():
    engine = DashboardEngine.from_config()
    view = engine.build_view(DashboardState(active_page=Page.MARKET_INTELLIGENCE), ReportBundle())
    assert view.valid is True
    assert all(spec.placeholder for spec in view.widgets.values())
