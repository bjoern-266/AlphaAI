"""Tests für das FVG-Muster."""

from __future__ import annotations

from patterns.base import PatternDirection
from patterns.fvg import FvgPattern
from tests.helpers import make_price_frame


def _params(min_gap_pct: float = 0.05) -> dict[str, float]:
    return {"min_gap_pct": min_gap_pct}


def test_bullish_fvg_detected_and_fresh() -> None:
    frame = make_price_frame(
        closes=[99.0, 109.0, 111.0],
        highs=[100.0, 110.0, 112.0],
        lows=[98.0, 101.0, 105.0],
    )
    detection = FvgPattern().detect(frame, _params())
    assert len(detection.patterns) == 1
    result = detection.patterns[0]
    assert result.direction is PatternDirection.BULLISH
    assert result.metadata["state"] == "fresh"
    assert result.metadata["gap_bottom"] == 100.0
    assert result.metadata["gap_top"] == 105.0


def test_bearish_fvg_detected() -> None:
    frame = make_price_frame(
        closes=[111.0, 101.0, 99.0],
        highs=[112.0, 109.0, 100.0],
        lows=[110.0, 99.0, 98.0],
    )
    detection = FvgPattern().detect(frame, _params())
    assert len(detection.patterns) == 1
    assert detection.patterns[0].direction is PatternDirection.BEARISH


def test_fvg_below_min_gap_is_filtered() -> None:
    # Winzige Lücke: 105.0 vs 105.001 -> weit unter 0.05 %.
    frame = make_price_frame(
        closes=[100.0, 104.0, 106.0],
        highs=[105.0, 105.5, 106.0],
        lows=[99.0, 104.0, 105.001],
    )
    detection = FvgPattern().detect(frame, _params(min_gap_pct=0.05))
    assert detection.patterns == []


def test_bullish_fvg_mitigated() -> None:
    # Vierte Kerze fällt unter den Gap-Boden (100) -> mitigated.
    frame = make_price_frame(
        closes=[99.0, 109.0, 111.0, 101.0],
        highs=[100.0, 110.0, 112.0, 102.0],
        lows=[98.0, 101.0, 105.0, 99.0],
    )
    detection = FvgPattern().detect(frame, _params())
    assert detection.patterns[0].metadata["state"] == "mitigated"


def test_fvg_min_candles() -> None:
    assert FvgPattern().min_candles(_params()) == 3
