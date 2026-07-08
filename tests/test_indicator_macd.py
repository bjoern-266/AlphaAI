"""Tests für den MACD-Indikator."""

from __future__ import annotations

import pytest

from indicators.macd import MacdIndicator
from tests.helpers import make_price_frame


def test_macd_constant_series_is_zero() -> None:
    out = MacdIndicator().compute(
        make_price_frame([100.0] * 60), {"fast": 12, "slow": 26, "signal": 9}
    )
    assert set(out.series) == {"macd", "signal", "histogram"}
    assert out.latest("macd") == pytest.approx(0.0, abs=1e-9)
    assert out.latest("histogram") == pytest.approx(0.0, abs=1e-9)


def test_macd_positive_in_uptrend() -> None:
    frame = make_price_frame([float(i) for i in range(1, 80)])
    out = MacdIndicator().compute(frame, {"fast": 12, "slow": 26, "signal": 9})
    macd = out.latest("macd")
    assert macd is not None and macd > 0


def test_macd_min_candles() -> None:
    assert MacdIndicator().min_candles({"fast": 12, "slow": 26, "signal": 9}) == 35
