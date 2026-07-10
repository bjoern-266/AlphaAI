"""Tests für den Buy-&-Hold-Benchmark (benchmark)."""

from __future__ import annotations

import pandas as pd

from backtesting.benchmark import buy_and_hold
from tests.helpers import make_price_frame


def test_buy_and_hold_positive_return():
    frame = make_price_frame([100.0, 110.0, 120.0])
    result = buy_and_hold(frame, 10000.0)
    assert result is not None
    assert result.start_price == 100.0
    assert result.end_price == 120.0
    assert round(result.return_pct, 2) == 20.0
    assert round(result.end_equity, 2) == 12000.0


def test_buy_and_hold_negative_return():
    frame = make_price_frame([100.0, 80.0])
    result = buy_and_hold(frame, 1000.0)
    assert result is not None
    assert round(result.return_pct, 2) == -20.0


def test_buy_and_hold_name_default():
    result = buy_and_hold(make_price_frame([10.0, 11.0]), 100.0)
    assert result is not None and result.name == "buy_and_hold"


def test_buy_and_hold_custom_name():
    result = buy_and_hold(make_price_frame([10.0, 11.0]), 100.0, name="spx")
    assert result is not None and result.name == "spx"


def test_buy_and_hold_fractional_shares_full_capital():
    # Startkapital 150 bei Preis 100 -> 1.5 Stück (Fractional Shares).
    frame = make_price_frame([100.0, 200.0])
    result = buy_and_hold(frame, 150.0)
    assert result is not None
    assert round(result.end_equity, 2) == 300.0


def test_buy_and_hold_empty_frame_none():
    assert buy_and_hold(pd.DataFrame(), 1000.0) is None


def test_buy_and_hold_missing_close_none():
    frame = pd.DataFrame({"open": [1.0, 2.0]})
    assert buy_and_hold(frame, 1000.0) is None


def test_buy_and_hold_zero_start_price_none():
    frame = make_price_frame([0.0, 100.0])
    assert buy_and_hold(frame, 1000.0) is None


def test_buy_and_hold_zero_capital_none():
    assert buy_and_hold(make_price_frame([100.0, 110.0]), 0.0) is None


def test_buy_and_hold_reason_is_transparent():
    result = buy_and_hold(make_price_frame([100.0, 110.0]), 1000.0)
    assert result is not None and result.reasons
    assert "Buy & Hold" in result.reasons[0]


def test_buy_and_hold_skips_leading_nan():
    frame = make_price_frame([100.0, 110.0, 121.0])
    frame.iloc[0, frame.columns.get_loc("close")] = float("nan")
    result = buy_and_hold(frame, 1000.0)
    # Erster gültiger Kurs ist 110, letzter 121.
    assert result is not None and result.start_price == 110.0
