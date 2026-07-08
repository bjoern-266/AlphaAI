"""Tests für den EMA-Indikator."""

from __future__ import annotations

import pytest

from indicators.ema import EmaIndicator
from tests.helpers import make_price_frame


def test_ema_constant_series_equals_constant() -> None:
    out = EmaIndicator().compute(make_price_frame([100.0] * 60), {"periods": [20, 50]})
    assert set(out.series) == {"ema_20", "ema_50"}
    assert out.latest("ema_20") == pytest.approx(100.0)
    assert out.latest("ema_50") == pytest.approx(100.0)


def test_ema_min_candles_is_smallest_period() -> None:
    assert EmaIndicator().min_candles({"periods": [20, 50, 200]}) == 20


def test_ema_longer_period_is_none_without_enough_history() -> None:
    # 60 Kerzen: EMA(20) real, EMA(200) mangels Historie None (NaN).
    out = EmaIndicator().compute(make_price_frame([100.0] * 60), {"periods": [20, 200]})
    assert out.latest("ema_20") is not None
    assert out.latest("ema_200") is None


def test_ema_missing_periods_raises() -> None:
    from indicators.base import IndicatorParameterError

    with pytest.raises(IndicatorParameterError):
        EmaIndicator().compute(make_price_frame([1.0, 2.0, 3.0]), {})
