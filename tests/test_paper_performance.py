"""Tests für die Performance-Kennzahlen (paper_trading.performance)."""

from __future__ import annotations

from paper_trading import performance as perf
from paper_trading.performance import PaperEquityPoint


def _perf(current_equity=10500.0, starting=10000.0):
    return perf.compute_performance(
        starting_capital=starting,
        current_equity=current_equity,
        realized_pnl=400.0,
        unrealized_pnl=100.0,
        running_drawdown_pct=1.0,
        maximum_drawdown_pct=3.0,
        exposure_pct=20.0,
        equity_curve=[PaperEquityPoint(None, 10000.0, 0.0, 0.0, 0)],
    )


def test_portfolio_return():
    assert _perf().portfolio_return_pct == 5.0


def test_negative_return():
    assert _perf(current_equity=9500.0).portfolio_return_pct == -5.0


def test_carries_drawdown_and_exposure():
    performance = _perf()
    assert performance.running_drawdown_pct == 1.0
    assert performance.maximum_drawdown_pct == 3.0
    assert performance.portfolio_exposure_pct == 20.0


def test_carries_pnl_split():
    performance = _perf()
    assert performance.realized_pnl == 400.0
    assert performance.unrealized_pnl == 100.0


def test_equity_curve_copied():
    performance = _perf()
    assert len(performance.equity_curve) == 1


def test_zero_capital_safe():
    performance = perf.compute_performance(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, [])
    assert performance.portfolio_return_pct == 0.0


def test_current_equity_field():
    assert _perf().current_equity == 10500.0


def test_starting_capital_field():
    assert _perf().starting_capital == 10000.0
