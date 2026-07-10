"""Tests für den Trade-Simulator (Ausstiegslogik, Fractional Shares, Kosten)."""

from __future__ import annotations

import pytest

from backtesting.trade_simulator import SimulationParams, TradeSimulator
from models.backtest import ExitReason, TradeOutcome
from models.recommendation import Direction
from tests.helpers import make_historical_signal, make_price_frame


def _sim(max_holding_bars=10, apply_costs=True, breakeven_epsilon=0.01):
    return TradeSimulator(
        SimulationParams(
            max_holding_bars=max_holding_bars,
            apply_costs=apply_costs,
            breakeven_epsilon=breakeven_epsilon,
        )
    )


def test_long_take_profit_exit():
    # entry 100, tp_distance 4 -> tp 104. Bar 1 high 105 trifft TP.
    frame = make_price_frame(
        [100.0, 104.0, 104.0], highs=[100.0, 105.0, 105.0], lows=[100.0, 101.0, 101.0]
    )
    signal = make_historical_signal(bar_index=0, entry_price=100.0)
    trades, _ = _sim().simulate([signal], frame, "AAPL")
    assert len(trades) == 1
    trade = trades[0]
    assert trade.exit_reason is ExitReason.TAKE_PROFIT
    assert trade.exit_price == 104.0
    assert trade.outcome is TradeOutcome.WIN
    # profit = (104-100)*10 - (1.0+0.5) = 38.5
    assert trade.profit == pytest.approx(38.5)


def test_long_stop_exit():
    frame = make_price_frame(
        [100.0, 97.0, 97.0], highs=[100.0, 100.0, 100.0], lows=[100.0, 97.0, 97.0]
    )
    signal = make_historical_signal(bar_index=0, entry_price=100.0)
    trades, _ = _sim().simulate([signal], frame, "AAPL")
    trade = trades[0]
    assert trade.exit_reason is ExitReason.STOP
    assert trade.exit_price == 98.0  # entry - stop_distance(2)
    assert trade.outcome is TradeOutcome.LOSS
    assert trade.profit == pytest.approx(-21.5)


def test_long_stop_has_priority_when_both_hit():
    # Bar 1 trifft sowohl Stop (low 97 <= 98) als auch TP (high 105 >= 104).
    frame = make_price_frame(
        [100.0, 100.0, 100.0], highs=[100.0, 105.0, 105.0], lows=[100.0, 97.0, 97.0]
    )
    signal = make_historical_signal(bar_index=0, entry_price=100.0)
    trades, _ = _sim().simulate([signal], frame, "AAPL")
    assert trades[0].exit_reason is ExitReason.STOP


def test_short_take_profit_exit():
    # SHORT entry 100, tp_distance 4 -> tp 96. Bar 1 low 95 trifft TP.
    frame = make_price_frame(
        [100.0, 96.0, 96.0], highs=[100.0, 100.0, 100.0], lows=[100.0, 95.0, 95.0]
    )
    signal = make_historical_signal(bar_index=0, entry_price=100.0, direction=Direction.SHORT)
    trades, _ = _sim().simulate([signal], frame, "AAPL")
    trade = trades[0]
    assert trade.exit_reason is ExitReason.TAKE_PROFIT
    assert trade.exit_price == 96.0
    assert trade.profit == pytest.approx(38.5)


def test_short_stop_exit():
    frame = make_price_frame(
        [100.0, 103.0, 103.0], highs=[100.0, 103.0, 103.0], lows=[100.0, 100.0, 100.0]
    )
    signal = make_historical_signal(bar_index=0, entry_price=100.0, direction=Direction.SHORT)
    trades, _ = _sim().simulate([signal], frame, "AAPL")
    trade = trades[0]
    assert trade.exit_reason is ExitReason.STOP
    assert trade.exit_price == 102.0
    assert trade.outcome is TradeOutcome.LOSS


def test_time_exit_when_no_threshold_hit():
    # Keine Kerze trifft Stop/TP; max_holding_bars 2 -> Zeit-Ausstieg.
    frame = make_price_frame(
        [100.0, 100.5, 101.0, 101.0, 101.0],
        highs=[100.0, 101.0, 101.5, 101.5, 101.5],
        lows=[100.0, 99.5, 100.5, 100.5, 100.5],
    )
    signal = make_historical_signal(bar_index=0, entry_price=100.0)
    trades, _ = _sim(max_holding_bars=2).simulate([signal], frame, "AAPL")
    trade = trades[0]
    assert trade.exit_reason is ExitReason.TIME
    assert trade.holding_bars == 2


def test_end_of_data_exit():
    frame = make_price_frame(
        [100.0, 100.5, 101.0],
        highs=[100.0, 101.0, 101.5],
        lows=[100.0, 99.5, 100.5],
    )
    signal = make_historical_signal(bar_index=0, entry_price=100.0)
    trades, _ = _sim(max_holding_bars=50).simulate([signal], frame, "AAPL")
    assert trades[0].exit_reason is ExitReason.END_OF_DATA


def test_breakeven_classification():
    # Zeit-Ausstieg exakt zum Einstiegskurs, keine Kosten -> BREAKEVEN.
    frame = make_price_frame(
        [100.0, 100.0, 100.0],
        highs=[100.0, 101.0, 101.0],
        lows=[100.0, 99.5, 99.5],
    )
    signal = make_historical_signal(bar_index=0, entry_price=100.0)
    trades, _ = _sim(max_holding_bars=1, apply_costs=False).simulate([signal], frame, "AAPL")
    assert trades[0].outcome is TradeOutcome.BREAKEVEN


def test_costs_reduce_profit_when_applied():
    frame = make_price_frame([100.0, 104.0], highs=[100.0, 105.0], lows=[100.0, 101.0])
    signal = make_historical_signal(bar_index=0, entry_price=100.0)
    with_costs, _ = _sim(apply_costs=True).simulate([signal], frame, "AAPL")
    without_costs, _ = _sim(apply_costs=False).simulate([signal], frame, "AAPL")
    assert without_costs[0].profit > with_costs[0].profit
    assert without_costs[0].commission == 0.0


def test_fractional_shares_supported():
    frame = make_price_frame([100.0, 104.0], highs=[100.0, 105.0], lows=[100.0, 101.0])
    signal = make_historical_signal(bar_index=0, entry_price=100.0, shares=2.5)
    trades, _ = _sim(apply_costs=False).simulate([signal], frame, "AAPL")
    # profit = (104-100)*2.5 = 10.0 (Bruchstücke erlaubt)
    assert trades[0].shares == 2.5
    assert trades[0].profit == pytest.approx(10.0)


def test_neutral_signal_produces_no_trade():
    frame = make_price_frame([100.0, 104.0], highs=[100.0, 105.0], lows=[100.0, 101.0])
    signal = make_historical_signal(bar_index=0, direction=Direction.NEUTRAL)
    trades, _ = _sim().simulate([signal], frame, "AAPL")
    assert trades == []


def test_only_one_position_at_a_time():
    frame = make_price_frame(
        [100.0, 100.5, 101.0, 101.5, 102.0, 102.5],
        highs=[100.0, 101.0, 101.5, 102.0, 102.5, 103.0],
        lows=[100.0, 99.5, 100.5, 101.0, 101.5, 102.0],
    )
    s0 = make_historical_signal(bar_index=0, entry_price=100.0)
    s1 = make_historical_signal(bar_index=1, entry_price=100.5)
    trades, _ = _sim(max_holding_bars=5).simulate([s0, s1], frame, "AAPL")
    # Zweites Signal fällt in die offene Position -> nur ein Trade.
    assert len(trades) == 1


def test_signal_at_last_bar_skipped_with_warning():
    frame = make_price_frame([100.0, 101.0], highs=[100.0, 102.0], lows=[100.0, 100.0])
    signal = make_historical_signal(bar_index=1, entry_price=101.0)  # letzte Kerze
    trades, warnings = _sim().simulate([signal], frame, "AAPL")
    assert trades == []
    assert any("kein" in w.lower() for w in warnings)


def test_empty_frame_returns_warning():
    import pandas as pd

    trades, warnings = _sim().simulate([make_historical_signal()], pd.DataFrame(), "AAPL")
    assert trades == []
    assert warnings


def test_trade_records_full_transparency():
    frame = make_price_frame([100.0, 104.0], highs=[100.0, 105.0], lows=[100.0, 101.0])
    signal = make_historical_signal(bar_index=0, entry_price=100.0)
    trades, _ = _sim().simulate([signal], frame, "AAPL")
    trade = trades[0]
    assert trade.entry_price == 100.0
    assert trade.stop_price == 98.0
    assert trade.take_profit_price == 104.0
    assert trade.risk_amount == pytest.approx(20.0)
    assert trade.recommendation_id == "rec:0"
    assert trade.direction is Direction.LONG
    assert trade.reasons == ["Testgrund"]
    assert trade.metadata["entry_index"] == 0


def test_holding_time_is_timedelta():
    frame = make_price_frame(
        [100.0, 100.5, 104.0], highs=[100.0, 101.0, 105.0], lows=[100.0, 99.5, 101.0]
    )
    signal = make_historical_signal(bar_index=0, entry_price=100.0)
    trades, _ = _sim().simulate([signal], frame, "AAPL")
    assert trades[0].holding_time is not None
    assert trades[0].holding_bars >= 1
