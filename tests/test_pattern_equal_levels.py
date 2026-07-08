"""Tests für Equal Highs und Equal Lows."""

from __future__ import annotations

from patterns.base import PatternDirection
from patterns.equal_highs import EqualHighsPattern
from patterns.equal_lows import EqualLowsPattern
from tests.helpers import make_price_frame


def test_equal_highs_detected() -> None:
    highs = [10.0, 15.0, 10.0, 15.0, 10.0]
    frame = make_price_frame([10.0, 12.0, 10.0, 12.0, 10.0], highs=highs, lows=[9.0] * 5)
    detection = EqualHighsPattern().detect(frame, {"swing_lookback": 1, "tolerance_pct": 0.1})
    assert len(detection.patterns) == 1
    result = detection.patterns[0]
    assert result.direction is PatternDirection.NEUTRAL
    assert result.price_level == 15.0


def test_equal_lows_detected() -> None:
    lows = [10.0, 5.0, 10.0, 5.0, 10.0]
    frame = make_price_frame([10.0, 8.0, 10.0, 8.0, 10.0], highs=[11.0] * 5, lows=lows)
    detection = EqualLowsPattern().detect(frame, {"swing_lookback": 1, "tolerance_pct": 0.1})
    assert len(detection.patterns) == 1
    assert detection.patterns[0].price_level == 5.0


def test_unequal_highs_not_detected() -> None:
    highs = [10.0, 15.0, 10.0, 20.0, 10.0]
    frame = make_price_frame([10.0, 12.0, 10.0, 12.0, 10.0], highs=highs, lows=[9.0] * 5)
    detection = EqualHighsPattern().detect(frame, {"swing_lookback": 1, "tolerance_pct": 0.1})
    assert detection.patterns == []


def test_equal_highs_min_candles() -> None:
    assert EqualHighsPattern().min_candles({"swing_lookback": 2, "tolerance_pct": 0.1}) == 5
