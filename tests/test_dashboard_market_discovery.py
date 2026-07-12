"""Tests der Market-Discovery-Dashboardseite (nur Anzeige des Reports)."""

from __future__ import annotations

from dashboard.engine import DashboardEngine
from dashboard.settings import DashboardSettings
from dashboard.state import DashboardState, Page
from dashboard.theme import load_theme
from dashboard.viewmodels import MarketDiscoveryVM, ReportBundle, build_view_model
from dashboard.widgets.base import WidgetContext
from dashboard.widgets.market_discovery import (
    DiscoveryRankingWidget,
    MarketBreakdownWidget,
    MarketOverviewWidget,
    SectorOverviewWidget,
    TopDiscoveryWidget,
)
from engines.market_discovery_engine import MarketDiscoveryEngine
from engines.market_intelligence_engine import MarketIntelligenceEngine
from models.dashboard import KIND_CARDS, KIND_TABLE
from models.recommendation import Direction, RecommendationStrength
from tests.market_discovery_helpers import (
    make_analysis,
    make_analysis_provider,
    make_symbol,
    make_symbol_source,
)

THEME = load_theme()
SETTINGS = DashboardSettings()


def _report():
    universe = {
        "sp500": [
            make_symbol("AAPL", company="Apple", sector="Tech", market="sp500"),
            make_symbol("NVDA", company="Nvidia", sector="Semi", market="sp500"),
        ],
        "dax": [make_symbol("SAP", company="SAP", sector="Software", country="DE", market="dax")],
    }
    analyses = {
        "AAPL": make_analysis("AAPL", Direction.LONG, RecommendationStrength.HIGH, 90.0, 80.0),
        "NVDA": make_analysis("NVDA", Direction.LONG, RecommendationStrength.VERY_HIGH, 92.0, 70.0),
        "SAP": make_analysis("SAP", Direction.SHORT, RecommendationStrength.MEDIUM, 55.0, 45.0),
    }
    engine = MarketDiscoveryEngine.from_config(intelligence=MarketIntelligenceEngine.from_config())
    return engine.discover(
        markets=["sp500", "dax"],
        symbol_source=make_symbol_source(universe),
        analysis_provider=make_analysis_provider(analyses),
    )


def _bundle():
    return ReportBundle(discovery=_report())


def _context(bundle: ReportBundle, state: DashboardState | None = None) -> WidgetContext:
    return WidgetContext(
        view_model=build_view_model(bundle),
        theme=THEME,
        settings=SETTINGS,
        state=state or DashboardState(),
    )


# --- View Model ------------------------------------------------------------ #


def test_vm_empty_without_report():
    vm = build_view_model(ReportBundle()).market_discovery
    assert isinstance(vm, MarketDiscoveryVM)
    assert vm.rows == ()
    assert vm.universe_count is None


def test_vm_reads_rows():
    vm = build_view_model(_bundle()).market_discovery
    assert len(vm.rows) == 3
    assert vm.rows[0].rank == 1


def test_vm_reads_statistics():
    vm = build_view_model(_bundle()).market_discovery
    assert vm.universe_count == 3
    assert vm.analyzed_count == 3
    assert vm.long_count == 2
    assert vm.short_count == 1


def test_vm_country_present():
    vm = build_view_model(_bundle()).market_discovery
    sap = next(row for row in vm.rows if row.ticker == "SAP")
    assert sap.country == "DE"


def test_vm_top_sectors_and_markets():
    vm = build_view_model(_bundle()).market_discovery
    assert vm.top_sectors
    assert vm.top_markets


# --- Widgets --------------------------------------------------------------- #


def test_top_discovery_table():
    spec = TopDiscoveryWidget().build(_context(_bundle()))
    assert spec.kind == KIND_TABLE
    assert spec.table is not None
    assert len(spec.table.rows) == 3
    assert not spec.placeholder


def test_top_discovery_placeholder_when_empty():
    spec = TopDiscoveryWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_ranking_table_metadata():
    spec = DiscoveryRankingWidget().build(_context(_bundle()))
    assert spec.metadata["total"] == 3


def test_ranking_search():
    state = DashboardState()
    state.set_search("AAPL")
    spec = DiscoveryRankingWidget().build(_context(_bundle(), state))
    assert spec.metadata["shown"] == 1


def test_ranking_direction_filter():
    state = DashboardState()
    state.set_filter("discovery_direction", "short")
    spec = DiscoveryRankingWidget().build(_context(_bundle(), state))
    assert spec.metadata["shown"] == 1


def test_ranking_market_filter():
    state = DashboardState()
    state.set_filter("discovery_market", "dax")
    spec = DiscoveryRankingWidget().build(_context(_bundle(), state))
    assert spec.metadata["shown"] == 1


def test_ranking_search_no_match():
    state = DashboardState()
    state.set_search("zzz")
    spec = DiscoveryRankingWidget().build(_context(_bundle(), state))
    assert spec.placeholder is True


def test_market_overview_cards():
    spec = MarketOverviewWidget().build(_context(_bundle()))
    assert spec.kind == KIND_CARDS
    assert len(spec.cards) == 9
    assert not spec.placeholder


def test_market_overview_placeholder():
    spec = MarketOverviewWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_sector_overview_table():
    spec = SectorOverviewWidget().build(_context(_bundle()))
    assert spec.kind == KIND_TABLE
    assert not spec.placeholder


def test_sector_overview_placeholder():
    spec = SectorOverviewWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_market_breakdown_table():
    spec = MarketBreakdownWidget().build(_context(_bundle()))
    assert spec.kind == KIND_TABLE
    assert not spec.placeholder


# --- Page über die Engine -------------------------------------------------- #


def test_engine_builds_market_discovery_page():
    engine = DashboardEngine.from_config()
    view = engine.build_view(DashboardState(active_page=Page.MARKET_DISCOVERY), _bundle())
    assert view.page == "market_discovery"
    assert view.valid is True
    assert set(view.widgets) == {
        "md_top_opportunities",
        "md_ranking",
        "md_sector_overview",
        "md_market_overview",
        "md_market_breakdown",
    }


def test_page_valid_with_empty_bundle():
    engine = DashboardEngine.from_config()
    view = engine.build_view(DashboardState(active_page=Page.MARKET_DISCOVERY), ReportBundle())
    assert view.valid is True
    assert all(spec.placeholder for spec in view.widgets.values())
