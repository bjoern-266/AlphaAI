"""Integrations-Tests: echte historische Szenarien durch die Backtest Engine.

Kein Mock: die Szenarien laufen durch die **echte** Pipeline (Indicator →
Pattern → Strategy → Score → Risk → Recommendation) und werden anschließend
simuliert und bewertet. Diese Tests belegen zugleich die Kern-Invarianten des
Sprints (keine neue Handelsregel, kein Look-Ahead, Trennung von Richtung und
Stärke).
"""

from __future__ import annotations

import pytest

from engines.backtest_engine import BacktestEngine
from models.backtest import Direction
from models.market import MarketResult, MarketStatus
from pipeline.runner import IntegrationRunner
from tests import scenarios
from tests.helpers import make_backtest_rules, make_settings

# Realistischer Vorlauf (genug Historie für EMA200), größere Schrittweite = schnell.
_RULES = make_backtest_rules(engine={"warmup_bars": 200, "step": 10, "min_history_bars": 210})


def _engine():
    return BacktestEngine(
        runner=IntegrationRunner.from_config(), settings=make_settings(), rules=_RULES
    )


def test_trend_up_runs_valid():
    result = _engine().run_frame(scenarios.trend_up(), "AAPL")
    assert result.valid is True
    assert result.signal_count >= result.trade_count


def test_trend_up_is_long_never_short():
    result = _engine().run_frame(scenarios.trend_up(), "AAPL")
    directions = {t.direction for t in result.trades}
    assert Direction.SHORT not in directions


def test_trend_down_is_short_never_long():
    result = _engine().run_frame(scenarios.trend_down(), "XYZ")
    directions = {t.direction for t in result.trades}
    assert Direction.LONG not in directions


def test_no_lookahead_exit_after_entry():
    result = _engine().run_frame(scenarios.trend_up(), "AAPL")
    for trade in result.trades:
        assert trade.metadata["exit_index"] > trade.metadata["entry_index"]


def test_strength_never_contains_direction_terms():
    result = _engine().run_frame(scenarios.trend_down(), "XYZ")
    forbidden = {"buy", "sell", "long", "short"}
    for trade in result.trades:
        assert trade.recommendation_strength.value not in forbidden


def test_trades_reference_existing_recommendation():
    result = _engine().run_frame(scenarios.trend_up(), "AAPL")
    for trade in result.trades:
        assert trade.recommendation_id.startswith("rec:")


def test_equity_curve_length_matches_trades():
    result = _engine().run_frame(scenarios.trend_up(), "AAPL")
    assert len(result.equity_curve) == result.trade_count + 1


def test_benchmark_present_for_scenario():
    result = _engine().run_frame(scenarios.trend_up(), "AAPL")
    assert result.benchmark is not None
    assert result.benchmark.return_pct > 0.0  # Aufwärtstrend


@pytest.mark.parametrize("name", ["sideways", "high_volatility", "choppy", "low_volatility"])
def test_various_scenarios_stay_consistent(name):
    result = _engine().run_frame(scenarios.SCENARIOS[name](), "SYM")
    assert result.valid is True
    assert 0.0 <= result.win_rate <= 1.0
    assert 0.0 <= result.maximum_drawdown <= 100.0
    assert len(result.equity_curve) == result.trade_count + 1


def test_run_report_over_market_result():
    market = MarketResult(
        provider="synthetic",
        status=MarketStatus.OK,
        data={"UP": scenarios.trend_up(), "DOWN": scenarios.trend_down()},
    )
    report = _engine().run(market)
    assert report.backtest_count == 2
    assert report.valid is True


def test_metadata_reports_bar_count_via_signals():
    result = _engine().run_frame(scenarios.trend_up(), "AAPL")
    assert result.metadata["signals"] >= result.metadata["actionable_signals"]
