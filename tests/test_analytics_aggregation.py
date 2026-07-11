"""Tests für die reinen Kennzahl-Bausteine (analytics.aggregation)."""

from __future__ import annotations

import math
from datetime import UTC, datetime

from analytics import aggregation as agg
from tests.helpers import make_analytics_trade


def _mix():
    """Zwei Gewinner (+100, +50) und ein Verlierer (-30)."""
    return [
        make_analytics_trade(trade_id="a", pnl=100.0, risk_reward=2.0, holding_days=2.0),
        make_analytics_trade(trade_id="b", pnl=50.0, risk_reward=3.0, holding_days=4.0),
        make_analytics_trade(trade_id="c", pnl=-30.0, risk_reward=1.0, holding_days=6.0),
    ]


def test_total_pnl():
    assert agg.total_pnl(_mix()) == 120.0


def test_win_rate():
    assert agg.win_rate(_mix()) == 2 / 3


def test_loss_rate():
    assert agg.loss_rate(_mix()) == 1 / 3


def test_rates_empty():
    assert agg.win_rate([]) == 0.0
    assert agg.loss_rate([]) == 0.0


def test_profit_factor():
    assert agg.profit_factor(_mix()) == 150.0 / 30.0


def test_profit_factor_no_losses_inf():
    assert math.isinf(agg.profit_factor([make_analytics_trade(pnl=10.0)]))


def test_profit_factor_empty():
    assert agg.profit_factor([]) == 0.0


def test_profit_factor_only_breakeven():
    assert agg.profit_factor([make_analytics_trade(pnl=0.0, outcome="breakeven")]) == 0.0


def test_average_winner():
    assert agg.average_winner(_mix()) == 75.0


def test_average_winner_none():
    assert agg.average_winner([make_analytics_trade(pnl=-5.0)]) == 0.0


def test_average_loser_negative():
    assert agg.average_loser(_mix()) == -30.0


def test_average_loser_none():
    assert agg.average_loser([make_analytics_trade(pnl=5.0)]) == 0.0


def test_average_return():
    assert agg.average_return(_mix()) == 40.0


def test_expectancy_equals_average_return():
    assert agg.expectancy(_mix()) == agg.average_return(_mix())


def test_average_holding_days():
    assert agg.average_holding_days(_mix()) == (2 + 4 + 6) / 3


def test_average_holding_days_empty():
    assert agg.average_holding_days([]) == 0.0


def test_average_risk_reward():
    assert agg.average_risk_reward(_mix()) == (2 + 3 + 1) / 3


def test_average_risk_reward_ignores_zero():
    assert agg.average_risk_reward([make_analytics_trade(risk_reward=0.0)]) == 0.0


def test_maximum_drawdown_empty():
    assert agg.maximum_drawdown_pct([]) == 0.0


def test_maximum_drawdown_no_loss_zero():
    assert agg.maximum_drawdown_pct([make_analytics_trade(pnl=100.0)]) == 0.0


def test_maximum_drawdown_value():
    d1 = datetime(2023, 1, 1, tzinfo=UTC)
    d2 = datetime(2023, 1, 2, tzinfo=UTC)
    trades = [
        make_analytics_trade(trade_id="a", pnl=100.0, exit_time=d1),
        make_analytics_trade(trade_id="b", pnl=-300.0, exit_time=d2),
    ]
    # base 10000 -> 10100 (peak) -> 9800 ; dd = 300/10100*100
    assert round(agg.maximum_drawdown_pct(trades, 10000.0), 4) == round(300 / 10100 * 100, 4)


def test_maximum_drawdown_base_zero():
    assert agg.maximum_drawdown_pct(_mix(), 0.0) == 0.0


def test_group_by():
    trades = [
        make_analytics_trade(direction=None, strategy="a"),
        make_analytics_trade(strategy="b"),
        make_analytics_trade(strategy="a"),
    ]
    groups = agg.group_by(trades, lambda t: t.strategy)
    assert set(groups) == {"a", "b"}
    assert len(groups["a"]) == 2


def test_group_statistics_fields():
    stat = agg.group_statistics("x", _mix())
    assert stat.label == "x"
    assert stat.trade_count == 3
    assert stat.win_rate == 2 / 3
    assert stat.total_pnl == 120.0


def test_group_statistics_empty():
    stat = agg.group_statistics("empty", [])
    assert stat.trade_count == 0
    assert stat.win_rate == 0.0


def test_grouped_statistics():
    trades = [make_analytics_trade(strategy="a"), make_analytics_trade(strategy="b", pnl=-10.0)]
    grouped = agg.grouped_statistics(trades, lambda t: t.strategy)
    assert set(grouped) == {"a", "b"}
    assert grouped["a"].win_rate == 1.0
    assert grouped["b"].loss_rate == 1.0


def test_chronological_orders_by_exit():
    d1 = datetime(2023, 1, 1, tzinfo=UTC)
    d2 = datetime(2023, 1, 5, tzinfo=UTC)
    late = make_analytics_trade(trade_id="late", exit_time=d2)
    early = make_analytics_trade(trade_id="early", exit_time=d1)
    ordered = agg.chronological([late, early])
    assert [t.trade_id for t in ordered] == ["early", "late"]
