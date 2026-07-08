"""Tests für das Liquidity-Sweep-Muster."""

from __future__ import annotations

from patterns.base import PatternDirection
from patterns.liquidity_sweep import LiquiditySweepPattern
from tests.helpers import make_price_frame


def test_bearish_sweep_of_swing_high() -> None:
    # Swing High bei Index 1 (High 15). Kerze 4 durchsticht (High 16) und
    # schließt darunter (Close 14) -> bärischer Sweep.
    frame = make_price_frame(
        closes=[10.0, 14.0, 10.0, 11.0, 14.0],
        highs=[10.0, 15.0, 10.0, 11.0, 16.0],
        lows=[9.0, 14.0, 9.0, 10.0, 13.0],
    )
    detection = LiquiditySweepPattern().detect(
        frame, {"swing_lookback": 1, "penetration_pct": 0.05}
    )
    assert len(detection.patterns) == 1
    assert detection.patterns[0].direction is PatternDirection.BEARISH


def test_bullish_sweep_of_swing_low() -> None:
    # Swing Low bei Index 1 (Low 5). Kerze 4 durchsticht (Low 4) und schließt
    # darüber (Close 6) -> bullischer Sweep.
    frame = make_price_frame(
        closes=[10.0, 6.0, 10.0, 9.0, 6.0],
        highs=[11.0, 7.0, 11.0, 10.0, 7.0],
        lows=[10.0, 5.0, 10.0, 9.0, 4.0],
    )
    detection = LiquiditySweepPattern().detect(
        frame, {"swing_lookback": 1, "penetration_pct": 0.05}
    )
    assert len(detection.patterns) == 1
    assert detection.patterns[0].direction is PatternDirection.BULLISH


def test_sweep_min_candles() -> None:
    assert LiquiditySweepPattern().min_candles({"swing_lookback": 2, "penetration_pct": 0.05}) == 6
