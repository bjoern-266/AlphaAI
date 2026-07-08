"""Tests für den Relative-Volume-Indikator."""

from __future__ import annotations

import pytest

from indicators.relative_volume import RelativeVolumeIndicator
from tests.helpers import make_price_frame


def test_rvol_constant_volume_is_one() -> None:
    frame = make_price_frame([100.0] * 30, volume=[1000.0] * 30)
    out = RelativeVolumeIndicator().compute(frame, {"period": 20})
    assert out.latest("relative_volume") == pytest.approx(1.0)


def test_rvol_spike_above_one() -> None:
    volume = [1000.0] * 29 + [5000.0]
    frame = make_price_frame([100.0] * 30, volume=volume)
    out = RelativeVolumeIndicator().compute(frame, {"period": 20})
    rvol = out.latest("relative_volume")
    assert rvol is not None and rvol > 1.0


def test_rvol_min_candles() -> None:
    assert RelativeVolumeIndicator().min_candles({"period": 20}) == 20
