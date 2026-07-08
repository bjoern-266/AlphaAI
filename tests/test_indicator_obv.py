"""Tests für den OBV-Indikator."""

from __future__ import annotations

import pytest

from indicators.obv import ObvIndicator
from tests.helpers import make_price_frame


def test_obv_accumulates_on_up_moves() -> None:
    frame = make_price_frame([100.0, 101.0, 102.0, 103.0], volume=[10.0, 20.0, 30.0, 40.0])
    out = ObvIndicator().compute(frame, {})
    # Erste Differenz = 0 (kein Vorwert), danach drei Aufwärtstage: 20+30+40 = 90.
    assert out.latest("obv") == pytest.approx(90.0)


def test_obv_decreases_on_down_moves() -> None:
    frame = make_price_frame([103.0, 102.0, 101.0, 100.0], volume=[10.0, 20.0, 30.0, 40.0])
    out = ObvIndicator().compute(frame, {})
    assert out.latest("obv") == pytest.approx(-90.0)


def test_obv_min_candles() -> None:
    assert ObvIndicator().min_candles({}) == 2
