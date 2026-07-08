"""Tests für Market Structure und Trend Structure."""

from __future__ import annotations

from patterns.base import PatternDirection
from patterns.market_structure import MarketStructurePattern
from patterns.trend_structure import TrendStructurePattern
from tests.helpers import make_price_frame


def test_market_structure_summary() -> None:
    prices = [10.0, 12.0, 11.0, 13.0, 9.0]
    frame = make_price_frame(prices, highs=prices, lows=prices)
    detection = MarketStructurePattern().detect(frame, {"swing_lookback": 1})
    assert len(detection.patterns) == 1
    result = detection.patterns[0]
    assert result.metadata["bos_count"] >= 1
    assert result.metadata["choch_count"] >= 1
    # Letzter Bruch war bärisch (CHoCH).
    assert result.direction is PatternDirection.BEARISH


def test_market_structure_without_breaks_is_neutral() -> None:
    prices = [10.0, 10.0, 10.0, 10.0, 10.0]
    frame = make_price_frame(prices, highs=prices, lows=prices)
    detection = MarketStructurePattern().detect(frame, {"swing_lookback": 1})
    assert detection.patterns[0].direction is PatternDirection.NEUTRAL
    assert detection.warnings


def test_trend_structure_uptrend() -> None:
    prices = [10.0, 13.0, 11.0, 15.0, 12.0, 17.0, 14.0, 19.0]
    frame = make_price_frame(prices, highs=prices, lows=prices)
    detection = TrendStructurePattern().detect(frame, {"swing_lookback": 1})
    assert len(detection.patterns) == 1
    result = detection.patterns[0]
    assert result.direction is PatternDirection.BULLISH
    assert result.metadata["trend"] == "uptrend"
    assert result.metadata["higher_high"] is True
    assert result.metadata["higher_low"] is True


def test_trend_structure_downtrend() -> None:
    prices = [20.0, 17.0, 19.0, 15.0, 18.0, 13.0, 16.0, 11.0]
    frame = make_price_frame(prices, highs=prices, lows=prices)
    detection = TrendStructurePattern().detect(frame, {"swing_lookback": 1})
    assert detection.patterns[0].direction is PatternDirection.BEARISH
    assert detection.patterns[0].metadata["trend"] == "downtrend"


def test_trend_structure_insufficient_swings() -> None:
    prices = [10.0, 11.0, 12.0, 13.0, 14.0]
    frame = make_price_frame(prices, highs=prices, lows=prices)
    detection = TrendStructurePattern().detect(frame, {"swing_lookback": 1})
    assert detection.patterns == []
    assert detection.warnings
