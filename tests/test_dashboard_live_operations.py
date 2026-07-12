"""Tests der Live-Operations-Dashboardseite (nur Anzeige des Reports)."""

from __future__ import annotations

from datetime import UTC, datetime

from dashboard.engine import DashboardEngine
from dashboard.settings import DashboardSettings
from dashboard.state import DashboardState, Page
from dashboard.theme import load_theme
from dashboard.viewmodels import LiveOperationsVM, ReportBundle, build_view_model
from dashboard.widgets.base import WidgetContext
from dashboard.widgets.live_operations import (
    JobHistoryWidget,
    MarketStatusWidget,
    NewSignalsWidget,
    ScanScheduleWidget,
    SystemStatusWidget,
    TopOpportunitiesWidget,
)
from models.dashboard import KIND_CARDS, KIND_LIST, KIND_STATUS, KIND_TABLE
from tests.operations_helpers import default_jobs, make_discovery_report, make_engine

THEME = load_theme()
SETTINGS = DashboardSettings()


def _report():
    def discovery():
        return make_discovery_report(("AAPL", "NVDA", "RISKY"), risky=("RISKY",))

    jobs = {**default_jobs(), "discovery": discovery}
    engine, _ = make_engine(clock_time=datetime(2024, 6, 3, 13, 35, tzinfo=UTC), jobs=jobs)
    return engine.tick()


def _bundle():
    return ReportBundle(operations=_report())


def _context(bundle: ReportBundle) -> WidgetContext:
    return WidgetContext(
        view_model=build_view_model(bundle),
        theme=THEME,
        settings=SETTINGS,
        state=DashboardState(),
    )


# --- View Model ------------------------------------------------------------ #


def test_vm_empty_without_report():
    vm = build_view_model(ReportBundle()).live_operations
    assert isinstance(vm, LiveOperationsVM)
    assert vm.markets == ()
    assert vm.health is None


def test_vm_reads_markets():
    vm = build_view_model(_bundle()).live_operations
    assert len(vm.markets) == 2
    assert {m.key for m in vm.markets} == {"europe", "us"}


def test_vm_reads_system_state():
    vm = build_view_model(_bundle()).live_operations
    assert vm.health == "ok"
    assert vm.heartbeat_alive is True
    assert vm.scan_count is not None


def test_vm_reads_top_rows():
    vm = build_view_model(_bundle()).live_operations
    assert len(vm.top_rows) == 3
    assert vm.top_rows[0].ticker == "AAPL"


def test_vm_new_signals():
    vm = build_view_model(_bundle()).live_operations
    assert "AAPL" in vm.new_opportunities
    assert "RISKY" in vm.new_risks


def test_vm_jobs():
    vm = build_view_model(_bundle()).live_operations
    assert len(vm.jobs) >= 1


def test_vm_next_scan():
    vm = build_view_model(_bundle()).live_operations
    assert vm.next_scan_job != ""


# --- Widgets --------------------------------------------------------------- #


def test_market_status_widget():
    spec = MarketStatusWidget().build(_context(_bundle()))
    assert spec.kind == KIND_STATUS
    assert len(spec.status_items) == 2
    assert not spec.placeholder


def test_market_status_placeholder():
    spec = MarketStatusWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_system_status_widget():
    spec = SystemStatusWidget().build(_context(_bundle()))
    assert spec.kind == KIND_CARDS
    assert len(spec.cards) == 8
    assert not spec.placeholder


def test_system_status_placeholder():
    spec = SystemStatusWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_schedule_widget():
    spec = ScanScheduleWidget().build(_context(_bundle()))
    assert spec.kind == KIND_CARDS
    assert not spec.placeholder


def test_schedule_placeholder():
    spec = ScanScheduleWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_top_opportunities_widget():
    spec = TopOpportunitiesWidget().build(_context(_bundle()))
    assert spec.kind == KIND_TABLE
    assert spec.table is not None
    assert len(spec.table.rows) == 3


def test_top_opportunities_placeholder():
    spec = TopOpportunitiesWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_new_signals_widget():
    spec = NewSignalsWidget().build(_context(_bundle()))
    assert spec.kind == KIND_LIST
    assert spec.items
    assert not spec.placeholder


def test_new_signals_placeholder():
    spec = NewSignalsWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


def test_job_history_widget():
    spec = JobHistoryWidget().build(_context(_bundle()))
    assert spec.kind == KIND_TABLE
    assert not spec.placeholder


def test_job_history_placeholder():
    spec = JobHistoryWidget().build(_context(ReportBundle()))
    assert spec.placeholder is True


# --- Page über die Engine -------------------------------------------------- #


def test_engine_builds_live_operations_page():
    engine = DashboardEngine.from_config()
    view = engine.build_view(DashboardState(active_page=Page.LIVE_OPERATIONS), _bundle())
    assert view.page == "live_operations"
    assert view.valid is True
    assert set(view.widgets) == {
        "lo_market_status",
        "lo_schedule",
        "lo_top_opportunities",
        "lo_job_history",
        "lo_system_status",
        "lo_new_signals",
    }


def test_page_valid_with_empty_bundle():
    engine = DashboardEngine.from_config()
    view = engine.build_view(DashboardState(active_page=Page.LIVE_OPERATIONS), ReportBundle())
    assert view.valid is True
    assert all(spec.placeholder for spec in view.widgets.values())
