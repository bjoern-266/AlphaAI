"""Tests für den Bollinger-Bänder-Indikator."""

from __future__ import annotations

import pytest

from indicators.bollinger import BollingerIndicator
from tests.helpers import make_price_frame


def test_bollinger_constant_series_has_zero_width() -> None:
    out = BollingerIndicator().compute(
        make_price_frame([100.0] * 30), {"period": 20, "std_dev": 2.0}
    )
    assert out.latest("upper") == pytest.approx(100.0)
    assert out.latest("middle") == pytest.approx(100.0)
    assert out.latest("lower") == pytest.approx(100.0)


def test_bollinger_upper_above_lower() -> None:
    frame = make_price_frame([100.0 + (i % 5) for i in range(40)])
    out = BollingerIndicator().compute(frame, {"period": 20, "std_dev": 2.0})
    assert out.latest("upper") > out.latest("lower")


def test_bollinger_min_candles() -> None:
    assert BollingerIndicator().min_candles({"period": 20, "std_dev": 2.0}) == 20
