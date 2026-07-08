"""Tests für gemeinsame Muster-Hilfsmittel (Swings, Struktur-Brüche)."""

from __future__ import annotations

from patterns.base import (
    PatternDirection,
    detect_structure_breaks,
    scaled_strength,
    swing_highs,
    swing_lows,
)
from tests.helpers import make_price_frame


def test_swing_highs_and_lows() -> None:
    frame = make_price_frame(
        [10.0, 15.0, 10.0, 8.0, 12.0],
        highs=[10.0, 15.0, 10.0, 8.0, 12.0],
        lows=[10.0, 15.0, 10.0, 8.0, 12.0],
    )
    assert swing_highs(frame, 1, 1) == [1]
    assert swing_lows(frame, 1, 1) == [3]


def test_structure_break_bos_then_choch() -> None:
    prices = [10.0, 12.0, 11.0, 13.0, 9.0]
    frame = make_price_frame(prices, highs=prices, lows=prices)
    events = detect_structure_breaks(frame, 1)
    kinds = [(e.kind, e.direction) for e in events]
    assert ("bos", PatternDirection.BULLISH) in kinds
    assert ("choch", PatternDirection.BEARISH) in kinds


def test_scaled_strength_bounds() -> None:
    assert scaled_strength(0.05, 0.05) == 100.0
    assert scaled_strength(0.10, 0.05) == 100.0  # begrenzt auf 100
    assert scaled_strength(0.0, 0.05) == 0.0
    assert scaled_strength(1.0, 0.0) == 0.0  # ungültige Skala
