"""Tests für die reinen Kennzahl-Funktionen (performance_metrics)."""

from __future__ import annotations

import math

from backtesting import performance_metrics as pm
from tests.helpers import make_simulated_trade


def _mix():
    """Zwei Gewinner (+100, +50) und ein Verlierer (-30)."""
    return [
        make_simulated_trade(trade_id="a", profit=100.0, risk_reward=2.0, holding_bars=2),
        make_simulated_trade(trade_id="b", profit=50.0, risk_reward=3.0, holding_bars=4),
        make_simulated_trade(trade_id="c", profit=-30.0, risk_reward=1.0, holding_bars=6),
    ]


def test_total_profit():
    assert pm.total_profit(_mix()) == 120.0


def test_gross_profit_and_loss():
    trades = _mix()
    assert pm.gross_profit(trades) == 150.0
    assert pm.gross_loss(trades) == 30.0


def test_win_rate():
    assert pm.win_rate(_mix()) == 2 / 3


def test_loss_rate():
    assert pm.loss_rate(_mix()) == 1 / 3


def test_win_rate_empty_is_zero():
    assert pm.win_rate([]) == 0.0
    assert pm.loss_rate([]) == 0.0


def test_profit_factor():
    assert pm.profit_factor(_mix()) == 150.0 / 30.0


def test_profit_factor_no_trades_zero():
    assert pm.profit_factor([]) == 0.0


def test_profit_factor_no_losses_is_inf():
    trades = [make_simulated_trade(profit=100.0)]
    assert math.isinf(pm.profit_factor(trades))


def test_profit_factor_only_breakeven_zero():
    trades = [make_simulated_trade(profit=0.0)]
    assert pm.profit_factor(trades) == 0.0


def test_average_win():
    assert pm.average_win(_mix()) == 75.0


def test_average_win_no_wins_zero():
    assert pm.average_win([make_simulated_trade(profit=-10.0)]) == 0.0


def test_average_loss_is_negative():
    assert pm.average_loss(_mix()) == -30.0


def test_average_loss_no_losses_zero():
    assert pm.average_loss([make_simulated_trade(profit=10.0)]) == 0.0


def test_average_risk_reward():
    assert pm.average_risk_reward(_mix()) == (2.0 + 3.0 + 1.0) / 3


def test_average_risk_reward_empty_zero():
    assert pm.average_risk_reward([]) == 0.0


def test_average_holding_time():
    assert pm.average_holding_time(_mix()) == (2 + 4 + 6) / 3


def test_expectancy_is_mean_profit():
    assert pm.expectancy(_mix()) == 120.0 / 3


def test_expectancy_empty_zero():
    assert pm.expectancy([]) == 0.0


def test_expectancy_r_uses_return_on_risk():
    trades = [
        make_simulated_trade(profit=40.0, risk_amount=20.0),  # R = 2
        make_simulated_trade(profit=-10.0, risk_amount=20.0),  # R = -0.5
    ]
    assert pm.expectancy_r(trades) == (2.0 + -0.5) / 2


def test_expectancy_r_ignores_zero_risk():
    trades = [make_simulated_trade(profit=40.0, risk_amount=0.0)]
    assert pm.expectancy_r(trades) == 0.0


def test_expectancy_equals_weighted_win_loss():
    trades = _mix()
    weighted = pm.win_rate(trades) * pm.average_win(trades) + pm.loss_rate(
        trades
    ) * pm.average_loss(trades)
    assert math.isclose(pm.expectancy(trades), weighted)
