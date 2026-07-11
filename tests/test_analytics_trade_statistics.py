"""Tests für das Trade-Statistics-Modell und den Performance-Analyzer."""

from __future__ import annotations

from analytics.performance_analyzer import PerformanceAnalyzer
from analytics.trade_statistics import TradeStatisticsModel
from models.recommendation import Direction
from tests.helpers import make_analytics_context, make_analytics_trade


def _trades():
    return [
        make_analytics_trade(trade_id="a", direction=Direction.LONG, pnl=100.0),
        make_analytics_trade(trade_id="b", direction=Direction.LONG, pnl=-40.0),
        make_analytics_trade(trade_id="c", direction=Direction.SHORT, pnl=60.0),
    ]


def test_trade_statistics_overall_metrics():
    out = TradeStatisticsModel().compute(make_analytics_context(trades=_trades()), {})
    assert out.metrics["trade_count"] == 3.0
    assert out.metrics["win_rate"] == 2 / 3
    assert out.metrics["profit_factor"] == 160.0 / 40.0


def test_trade_statistics_long_short_split():
    out = TradeStatisticsModel().compute(make_analytics_context(trades=_trades()), {})
    assert out.statistics["long"].trade_count == 2
    assert out.statistics["short"].trade_count == 1


def test_trade_statistics_expectancy():
    out = TradeStatisticsModel().compute(make_analytics_context(trades=_trades()), {})
    assert out.metrics["expectancy"] == 120.0 / 3


def test_trade_statistics_empty_warns():
    out = TradeStatisticsModel().compute(make_analytics_context(trades=[]), {})
    assert out.metrics["trade_count"] == 0.0
    assert out.warnings


def test_trade_statistics_avg_risk_reward():
    out = TradeStatisticsModel().compute(make_analytics_context(trades=_trades()), {})
    assert out.metrics["average_risk_reward"] == 2.0


def test_trade_statistics_overall_group_present():
    out = TradeStatisticsModel().compute(make_analytics_context(trades=_trades()), {})
    assert out.statistics["overall"].trade_count == 3


def test_performance_metrics():
    out = PerformanceAnalyzer().compute(make_analytics_context(trades=_trades()), {})
    assert out.metrics["total_pnl"] == 120.0
    assert out.metrics["base_capital"] == 10000.0
    assert round(out.metrics["total_return_pct"], 4) == round(120.0 / 10000.0 * 100.0, 4)


def test_performance_best_worst():
    out = PerformanceAnalyzer().compute(make_analytics_context(trades=_trades()), {})
    assert out.metrics["best_trade"] == 100.0
    assert out.metrics["worst_trade"] == -40.0


def test_performance_equity_curve():
    out = PerformanceAnalyzer().compute(make_analytics_context(trades=_trades()), {})
    curve = out.details["equity_curve"]
    assert curve[0] == 10000.0
    assert len(curve) == 4  # Start + 3 Trades
    assert curve[-1] == out.metrics["final_equity"]


def test_performance_empty():
    out = PerformanceAnalyzer().compute(make_analytics_context(trades=[]), {})
    assert out.metrics["total_pnl"] == 0.0
    assert out.metrics["final_equity"] == 10000.0


def test_performance_respects_base_capital_config():
    ctx = make_analytics_context(trades=_trades(), config={"base_capital": 5000.0})
    out = PerformanceAnalyzer().compute(ctx, {})
    assert out.metrics["base_capital"] == 5000.0
    assert round(out.metrics["total_return_pct"], 4) == round(120.0 / 5000.0 * 100.0, 4)
