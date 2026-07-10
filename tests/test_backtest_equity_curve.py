"""Tests für die Kapitalkurve und den Drawdown (equity_curve)."""

from __future__ import annotations

from backtesting import equity_curve as ec
from tests.helpers import make_simulated_trade


def test_empty_trades_single_start_point():
    curve = ec.build_equity_curve([], 10000.0)
    assert len(curve) == 1
    assert curve[0].equity == 10000.0
    assert curve[0].drawdown == 0.0
    assert curve[0].drawdown_pct == 0.0


def test_curve_grows_with_profit():
    trades = [make_simulated_trade(profit=100.0), make_simulated_trade(profit=50.0)]
    curve = ec.build_equity_curve(trades, 1000.0)
    assert [round(p.equity, 2) for p in curve] == [1000.0, 1100.0, 1150.0]


def test_final_equity():
    trades = [make_simulated_trade(profit=100.0)]
    curve = ec.build_equity_curve(trades, 1000.0)
    assert ec.final_equity(curve, 1000.0) == 1100.0


def test_final_equity_empty_curve_returns_capital():
    assert ec.final_equity([], 5000.0) == 5000.0


def test_drawdown_tracks_peak():
    trades = [
        make_simulated_trade(trade_id="a", profit=100.0),  # 1100 (peak)
        make_simulated_trade(trade_id="b", profit=-200.0),  # 900 -> dd 200
    ]
    curve = ec.build_equity_curve(trades, 1000.0)
    assert curve[-1].drawdown == 200.0
    assert round(curve[-1].drawdown_pct, 4) == round(200.0 / 1100.0 * 100.0, 4)


def test_maximum_drawdown_pct():
    trades = [
        make_simulated_trade(trade_id="a", profit=100.0),
        make_simulated_trade(trade_id="b", profit=-300.0),
        make_simulated_trade(trade_id="c", profit=50.0),
    ]
    curve = ec.build_equity_curve(trades, 1000.0)
    assert round(ec.maximum_drawdown(curve), 4) == round(300.0 / 1100.0 * 100.0, 4)


def test_maximum_drawdown_abs():
    trades = [
        make_simulated_trade(trade_id="a", profit=100.0),
        make_simulated_trade(trade_id="b", profit=-300.0),
    ]
    curve = ec.build_equity_curve(trades, 1000.0)
    assert ec.maximum_drawdown_abs(curve) == 300.0


def test_no_drawdown_when_only_gains():
    trades = [make_simulated_trade(profit=100.0), make_simulated_trade(profit=100.0)]
    curve = ec.build_equity_curve(trades, 1000.0)
    assert ec.maximum_drawdown(curve) == 0.0


def test_maximum_drawdown_empty_curve():
    assert ec.maximum_drawdown([]) == 0.0
    assert ec.maximum_drawdown_abs([]) == 0.0


def test_curve_sorted_by_exit_time():
    from datetime import UTC, datetime

    late = make_simulated_trade(
        trade_id="late", profit=10.0, exit_time=datetime(2023, 2, 1, tzinfo=UTC)
    )
    early = make_simulated_trade(
        trade_id="early", profit=-5.0, exit_time=datetime(2023, 1, 1, tzinfo=UTC)
    )
    curve = ec.build_equity_curve([late, early], 1000.0)
    # Frühester Trade zuerst: 1000 -> 995 -> 1005.
    assert [round(p.equity, 2) for p in curve] == [1000.0, 995.0, 1005.0]


def test_start_time_carried_into_first_point():
    from datetime import UTC, datetime

    start = datetime(2023, 1, 1, tzinfo=UTC)
    curve = ec.build_equity_curve([], 1000.0, start_time=start)
    assert curve[0].timestamp == start
