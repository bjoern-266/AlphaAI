"""Tests für BOS- und CHoCH-Muster."""

from __future__ import annotations

from patterns.base import PatternDirection
from patterns.bos import BosPattern
from patterns.choch import ChochPattern
from tests.helpers import make_price_frame

# Sequenz erzeugt bei swing_lookback=1 einen bullischen BOS und danach einen
# bärischen CHoCH.
_PRICES = [10.0, 12.0, 11.0, 13.0, 9.0]


def _frame() -> object:
    return make_price_frame(_PRICES, highs=_PRICES, lows=_PRICES)


def test_bos_detects_only_bos() -> None:
    detection = BosPattern().detect(_frame(), {"swing_lookback": 1})
    assert len(detection.patterns) == 1
    result = detection.patterns[0]
    assert result.direction is PatternDirection.BULLISH
    assert result.metadata["break_level"] == 12.0


def test_choch_detects_only_choch() -> None:
    detection = ChochPattern().detect(_frame(), {"swing_lookback": 1})
    assert len(detection.patterns) == 1
    assert detection.patterns[0].direction is PatternDirection.BEARISH


def test_bos_min_candles() -> None:
    assert BosPattern().min_candles({"swing_lookback": 2}) == 5


def test_choch_min_candles() -> None:
    assert ChochPattern().min_candles({"swing_lookback": 2}) == 5
