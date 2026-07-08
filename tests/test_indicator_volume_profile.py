"""Tests für den Volume-Profile-Indikator."""

from __future__ import annotations

import pytest

from indicators.volume_profile import VolumeProfileIndicator
from tests.helpers import make_price_frame


def test_volume_profile_preserves_total_volume() -> None:
    frame = make_price_frame(
        [100.0, 101.0, 102.0, 103.0, 104.0], volume=[10.0, 20.0, 30.0, 40.0, 50.0]
    )
    out = VolumeProfileIndicator().compute(frame, {"bins": 5})
    profile = out.series["volume_profile"]
    assert profile.sum() == pytest.approx(150.0)
    assert out.extra["poc"] is not None


def test_volume_profile_constant_price_single_level() -> None:
    frame = make_price_frame([100.0] * 5, volume=[10.0] * 5)
    out = VolumeProfileIndicator().compute(frame, {"bins": 5})
    assert out.extra["poc"] == pytest.approx(100.0)
    assert len(out.warnings) == 1


def test_volume_profile_poc_at_highest_volume() -> None:
    # Höchstes Volumen liegt am höchsten Kurs -> POC nahe diesem Preis.
    frame = make_price_frame(
        [100.0, 101.0, 102.0, 103.0, 104.0], volume=[1.0, 1.0, 1.0, 1.0, 100.0]
    )
    out = VolumeProfileIndicator().compute(frame, {"bins": 5})
    assert out.extra["poc"] > 102.0
