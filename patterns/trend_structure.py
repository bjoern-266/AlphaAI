"""Trend Structure – Higher/Lower Highs und Lows sowie Trend.

Vergleicht die letzten beiden Swing Highs und Swing Lows und leitet daraus
Higher High, Higher Low, Lower High, Lower Low und den resultierenden Trend
ab. Unabhängig von allen anderen Mustern.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from patterns.base import (
    BasePattern,
    PatternDetection,
    PatternDirection,
    PatternResult,
    PatternType,
    require_int,
    swing_highs,
    swing_lows,
)


class TrendStructurePattern(BasePattern):
    """Detektor für die Trendstruktur (HH/HL/LH/LL)."""

    name = "trend_structure"
    pattern_type = PatternType.TREND

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt genug Kerzen für je zwei Swing-Hochs und -Tiefs."""
        return 2 * require_int(params, "swing_lookback", self.name) + 1

    def detect(self, data: pd.DataFrame, params: Mapping[str, Any]) -> PatternDetection:
        """Ermittelt HH/HL/LH/LL und den daraus folgenden Trend."""
        lookback = require_int(params, "swing_lookback", self.name)
        detection = PatternDetection()

        highs = swing_highs(data, lookback, lookback)
        lows = swing_lows(data, lookback, lookback)
        if len(highs) < 2 or len(lows) < 2:
            detection.warnings.append("Zu wenige Swings für eine Trendstruktur.")
            return detection

        high = data["high"]
        low = data["low"]
        higher_high = float(high.iloc[highs[-1]]) > float(high.iloc[highs[-2]])
        lower_high = float(high.iloc[highs[-1]]) < float(high.iloc[highs[-2]])
        higher_low = float(low.iloc[lows[-1]]) > float(low.iloc[lows[-2]])
        lower_low = float(low.iloc[lows[-1]]) < float(low.iloc[lows[-2]])

        if higher_high and higher_low:
            direction = PatternDirection.BULLISH
            trend = "uptrend"
        elif lower_high and lower_low:
            direction = PatternDirection.BEARISH
            trend = "downtrend"
        else:
            direction = PatternDirection.NEUTRAL
            trend = "range"

        detection.patterns.append(
            PatternResult(
                name=self.name,
                pattern_type=self.pattern_type,
                direction=direction,
                strength=100.0 if direction is not PatternDirection.NEUTRAL else 40.0,
                confidence=0.6,
                timestamp=data.index[-1],
                price_level=float(data["close"].iloc[-1]),
                metadata={
                    "higher_high": higher_high,
                    "higher_low": higher_low,
                    "lower_high": lower_high,
                    "lower_low": lower_low,
                    "trend": trend,
                },
            )
        )
        return detection
