"""Tests für den Stochastik-Indikator."""

from __future__ import annotations

from indicators.stochastic import StochasticIndicator
from tests.helpers import make_price_frame


def test_stochastic_high_in_uptrend() -> None:
    frame = make_price_frame([float(i) for i in range(1, 40)])
    out = StochasticIndicator().compute(frame, {"k_period": 14, "d_period": 3, "smooth_k": 3})
    assert set(out.series) == {"percent_k", "percent_d"}
    percent_k = out.latest("percent_k")
    assert percent_k is not None and percent_k > 80.0


def test_stochastic_low_in_downtrend() -> None:
    frame = make_price_frame([float(i) for i in range(40, 1, -1)])
    out = StochasticIndicator().compute(frame, {"k_period": 14, "d_period": 3, "smooth_k": 3})
    percent_k = out.latest("percent_k")
    assert percent_k is not None and percent_k < 20.0


def test_stochastic_min_candles() -> None:
    assert StochasticIndicator().min_candles({"k_period": 14, "d_period": 3, "smooth_k": 3}) == 20
