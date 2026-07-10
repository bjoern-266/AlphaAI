"""Tests für die Handelsstatistik (paper_trading.statistics)."""

from __future__ import annotations

import math

from paper_trading import statistics as st
from tests.helpers import make_paper_trade


def _mix():
    """Zwei Gewinner (+100, +50) und ein Verlierer (-30)."""
    return [
        make_paper_trade(trade_id="a", pnl=100.0, holding_days=2.0),
        make_paper_trade(trade_id="b", pnl=50.0, holding_days=4.0),
        make_paper_trade(trade_id="c", pnl=-30.0, holding_days=6.0),
    ]


def test_win_rate():
    assert st.win_rate(_mix()) == 2 / 3


def test_loss_rate():
    assert st.loss_rate(_mix()) == 1 / 3


def test_rates_empty():
    assert st.win_rate([]) == 0.0
    assert st.loss_rate([]) == 0.0


def test_profit_factor():
    assert st.profit_factor(_mix()) == 150.0 / 30.0


def test_profit_factor_no_losses_inf():
    assert math.isinf(st.profit_factor([make_paper_trade(pnl=10.0)]))


def test_profit_factor_empty_zero():
    assert st.profit_factor([]) == 0.0


def test_average_winner():
    assert st.average_winner(_mix()) == 75.0


def test_average_winner_none_zero():
    assert st.average_winner([make_paper_trade(pnl=-5.0)]) == 0.0


def test_average_loser_negative():
    assert st.average_loser(_mix()) == -30.0


def test_average_loser_none_zero():
    assert st.average_loser([make_paper_trade(pnl=5.0)]) == 0.0


def test_average_holding_time():
    assert st.average_holding_time(_mix()) == (2.0 + 4.0 + 6.0) / 3


def test_average_holding_time_empty():
    assert st.average_holding_time([]) == 0.0


def test_compute_statistics_counts_and_return():
    stats = st.compute_statistics(
        trades=_mix(),
        open_positions=2,
        closed_positions=3,
        current_equity=10120.0,
        starting_capital=10000.0,
    )
    assert stats.open_positions == 2
    assert stats.closed_positions == 3
    assert stats.current_equity == 10120.0
    assert stats.portfolio_return_pct == 1.2
    assert stats.win_rate == 2 / 3


def test_compute_statistics_zero_capital_safe():
    stats = st.compute_statistics([], 0, 0, 0.0, 0.0)
    assert stats.portfolio_return_pct == 0.0


def test_compute_statistics_empty_neutral():
    stats = st.compute_statistics([], 0, 0, 10000.0, 10000.0)
    assert stats.win_rate == 0.0
    assert stats.profit_factor == 0.0
