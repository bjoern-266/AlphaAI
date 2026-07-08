"""Tests für den ATR-Indikator."""

from __future__ import annotations

import pytest

from indicators.atr import AtrIndicator
from tests.helpers import make_price_frame


def test_atr_constant_range_converges() -> None:
    # High = Close + 1, Low = Close - 1 -> True Range = 2 auf jeder Kerze.
    out = AtrIndicator().compute(make_price_frame([100.0] * 40), {"period": 14})
    assert out.latest("atr_14") == pytest.approx(2.0, abs=1e-6)


def test_atr_min_candles() -> None:
    assert AtrIndicator().min_candles({"period": 14}) == 15


def test_atr_is_non_negative() -> None:
    frame = make_price_frame([float(i) for i in range(1, 40)])
    out = AtrIndicator().compute(frame, {"period": 14})
    atr = out.latest("atr_14")
    assert atr is not None and atr >= 0
