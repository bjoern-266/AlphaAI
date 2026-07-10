"""Tests für die (vorbereiteten) risikoadjustierten Kennzahlen (statistics)."""

from __future__ import annotations

import math

from backtesting import statistics as st
from tests.helpers import make_simulated_trade


def test_trade_returns_uses_profit_pct():
    trades = [make_simulated_trade(profit=100.0, position_value=1000.0)]
    # profit_pct = 10 % -> return 0.10
    assert st.trade_returns(trades) == [0.10]


def test_sharpe_none_with_less_than_two():
    assert st.sharpe_ratio([0.05]) is None
    assert st.sharpe_ratio([]) is None


def test_sharpe_none_when_zero_std():
    assert st.sharpe_ratio([0.02, 0.02, 0.02]) is None


def test_sharpe_positive_for_positive_returns():
    ratio = st.sharpe_ratio([0.01, 0.02, 0.03])
    assert ratio is not None and ratio > 0


def test_sharpe_annualized_scales_up():
    plain = st.sharpe_ratio([0.01, 0.02, 0.03])
    annual = st.sharpe_ratio([0.01, 0.02, 0.03], periods_per_year=252)
    assert annual is not None and plain is not None
    assert math.isclose(annual, plain * math.sqrt(252))


def test_sortino_none_with_less_than_two():
    assert st.sortino_ratio([0.05]) is None


def test_sortino_none_without_downside():
    # Keine Abwärtsbewegung -> downside dev = 0 -> None.
    assert st.sortino_ratio([0.01, 0.02, 0.03]) is None


def test_sortino_defined_with_downside():
    ratio = st.sortino_ratio([0.03, -0.02, 0.01])
    assert ratio is not None


def test_calmar_none_without_drawdown():
    assert st.calmar_ratio(10.0, 0.0) is None
    assert st.calmar_ratio(10.0, -5.0) is None


def test_calmar_ratio_value():
    assert st.calmar_ratio(20.0, 10.0) == 2.0


def test_sharpe_risk_free_reduces_ratio():
    high = st.sharpe_ratio([0.02, 0.04, 0.06])
    low = st.sharpe_ratio([0.02, 0.04, 0.06], risk_free_rate=0.02)
    assert high is not None and low is not None
    assert low < high
