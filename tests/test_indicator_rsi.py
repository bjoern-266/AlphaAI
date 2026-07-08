"""Tests für den RSI-Indikator."""

from __future__ import annotations

import pytest

from indicators.rsi import RsiIndicator
from tests.helpers import make_price_frame


def test_rsi_rising_series_is_hundred() -> None:
    frame = make_price_frame([float(i) for i in range(1, 40)])
    out = RsiIndicator().compute(frame, {"period": 14})
    assert out.latest("rsi_14") == pytest.approx(100.0)


def test_rsi_falling_series_is_zero() -> None:
    frame = make_price_frame([float(i) for i in range(40, 1, -1)])
    out = RsiIndicator().compute(frame, {"period": 14})
    assert out.latest("rsi_14") == pytest.approx(0.0)


def test_rsi_min_candles() -> None:
    assert RsiIndicator().min_candles({"period": 14}) == 15
