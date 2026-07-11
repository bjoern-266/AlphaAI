"""Tests der View Models (lesen Reports ab, berechnen nichts)."""

from __future__ import annotations

import dataclasses

import pytest

from dashboard.state import SystemStatus
from dashboard.viewmodels import (
    DashboardViewModel,
    ReportBundle,
    build_view_model,
)
from engines.indicator_result import IndicatorResult
from tests.dashboard_helpers import (
    make_analytics_report,
    make_backtest_report,
    make_paper_report,
    make_recommendation_report,
)


def _full_bundle() -> ReportBundle:
    return ReportBundle(
        recommendation=make_recommendation_report(),
        paper_trading=make_paper_report(),
        backtest=make_backtest_report(),
        analytics=make_analytics_report(),
        indicator=IndicatorResult(outputs={}, valid=True, metadata={}),
    )


def test_empty_bundle_builds_valid_view_model():
    vm = build_view_model(ReportBundle())
    assert isinstance(vm, DashboardViewModel)
    assert vm.overview.current_equity is None
    assert vm.live.rows == ()
    assert vm.backtest.trades == ()


def test_view_model_is_frozen():
    vm = build_view_model(ReportBundle())
    with pytest.raises(dataclasses.FrozenInstanceError):
        vm.overview = None  # type: ignore[misc]


def test_overview_reads_paper_and_analytics():
    vm = build_view_model(_full_bundle())
    assert vm.overview.current_equity == 10_360.0
    assert vm.overview.profit_factor == 1.7  # aus AnalyticsResult
    assert vm.overview.win_rate == 0.55
    assert vm.overview.recommendation_count == 2


def test_overview_todays_pnl_is_placeholder_none():
    # Today's PnL wird in keinem Report gespeichert -> None (kein Ersatzwert).
    vm = build_view_model(_full_bundle())
    assert vm.overview.todays_pnl is None


def test_overview_statuses_online_when_present():
    vm = build_view_model(_full_bundle())
    statuses = {s.name: s.status for s in vm.overview.statuses}
    assert statuses["Analytics"] == SystemStatus.ONLINE.value
    assert statuses["Paper Trading"] == SystemStatus.ONLINE.value


def test_overview_statuses_offline_when_absent():
    vm = build_view_model(ReportBundle())
    statuses = {s.name: s.status for s in vm.overview.statuses}
    assert statuses["Analytics"] == SystemStatus.OFFLINE.value
    assert statuses["Market Data"] == SystemStatus.OFFLINE.value


def test_portfolio_reads_performance():
    vm = build_view_model(_full_bundle())
    assert vm.portfolio.current_equity == 10_360.0
    assert vm.portfolio.realized_pnl == 360.0
    assert vm.portfolio.unrealized_pnl == 90.0
    assert vm.portfolio.open_positions == 1
    assert vm.portfolio.closed_positions == 5


def test_portfolio_equity_curve_read():
    vm = build_view_model(_full_bundle())
    assert len(vm.portfolio.equity_curve) == 4
    assert vm.portfolio.equity_curve[0] == 10_000.0
    assert len(vm.portfolio.equity_labels) == 4


def test_portfolio_cash_is_placeholder_none():
    vm = build_view_model(_full_bundle())
    assert vm.portfolio.cash is None


def test_backtest_reads_first_result():
    vm = build_view_model(_full_bundle())
    assert vm.backtest.profit_factor == 1.9
    assert vm.backtest.win_rate == 0.66
    assert vm.backtest.total_return_pct == 2.4
    assert vm.backtest.benchmark_name == "buy_and_hold"
    assert vm.backtest.benchmark_return == 12.0


def test_backtest_trades_read():
    vm = build_view_model(_full_bundle())
    assert len(vm.backtest.trades) == 3
    trade = vm.backtest.trades[0]
    assert trade.symbol == "AAPL"
    assert trade.direction == "long"


def test_backtest_empty_without_results():
    from models.backtest import BacktestReport

    vm = build_view_model(ReportBundle(backtest=BacktestReport(results=[])))
    assert vm.backtest.trades == ()
    assert vm.backtest.profit_factor is None


def test_live_rows_from_recommendation():
    vm = build_view_model(_full_bundle())
    assert len(vm.live.rows) == 2
    row = vm.live.rows[0]
    assert row.symbol == "AAPL"
    assert row.direction == "long"
    assert row.risk == 30.0  # roher Faktorwert, keine Ableitung


def test_live_reasons_and_warnings_read():
    vm = build_view_model(_full_bundle())
    row = vm.live.rows[0]
    assert "Trend intakt" in row.reasons
    assert "Spread erhöht" in row.warnings


def test_analytics_reads_result_directly():
    vm = build_view_model(_full_bundle())
    assert vm.analytics.trade_count == 8
    assert vm.analytics.profit_factor == 1.7
    assert vm.analytics.long_statistics.trade_count == 5
    assert vm.analytics.short_statistics.trade_count == 3
    assert "trend_following" in vm.analytics.strategy_statistics
    assert vm.analytics.summary == "Analyse abgeschlossen."


def test_analytics_time_statistics_read():
    vm = build_view_model(_full_bundle())
    assert "weekday" in vm.analytics.time_statistics
    assert "holding" in vm.analytics.time_statistics


def test_analytics_empty_without_report():
    vm = build_view_model(ReportBundle())
    assert vm.analytics.trade_count is None
    assert vm.analytics.long_statistics is None


def test_performance_reads_curves():
    vm = build_view_model(_full_bundle())
    assert len(vm.performance.equity_curve) == 4
    assert len(vm.performance.drawdown_curve) == 4
    assert len(vm.performance.profit_distribution) == 3  # aus Backtest-Trades


def test_performance_holding_from_analytics():
    vm = build_view_model(_full_bundle())
    assert vm.performance.holding_labels == ("1-3",)
    assert vm.performance.holding_counts == (4.0,)


def test_journal_rows_read():
    vm = build_view_model(_full_bundle())
    assert len(vm.journal.rows) == 2
    assert vm.journal.rows[0].action in ("open", "close")


def test_recommendations_rows_read():
    vm = build_view_model(_full_bundle())
    assert len(vm.recommendations.rows) == 2
    row = vm.recommendations.rows[0]
    assert row.symbol == "AAPL"
    assert row.risk == 30.0
    assert row.summary


def test_recommendations_empty_without_report():
    vm = build_view_model(ReportBundle())
    assert vm.recommendations.rows == ()


def test_report_bundle_all_optional():
    bundle = ReportBundle()
    assert bundle.analytics is None
    assert bundle.paper_trading is None
    assert bundle.backtest is None
    assert bundle.recommendation is None


def test_report_bundle_is_frozen():
    bundle = ReportBundle()
    with pytest.raises(dataclasses.FrozenInstanceError):
        bundle.analytics = None  # type: ignore[misc]
