"""Equal Lows – annähernd gleiche Swing-Tiefs (Liquidität unterhalb).

Erkennt Paare aufeinanderfolgender Swing Lows, deren Preise innerhalb einer
Toleranz gleich sind. Unabhängig von allen anderen Mustern.
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
    require_float,
    require_int,
    swing_lows,
)


class EqualLowsPattern(BasePattern):
    """Detektor für annähernd gleiche Swing-Tiefs."""

    name = "equal_lows"
    pattern_type = PatternType.EQUAL_LEVEL

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt genug Kerzen für mindestens zwei Swings."""
        return 2 * require_int(params, "swing_lookback", self.name) + 1

    def detect(self, data: pd.DataFrame, params: Mapping[str, Any]) -> PatternDetection:
        """Erkennt Paare gleich tiefer Swing-Tiefs innerhalb der Toleranz."""
        lookback = require_int(params, "swing_lookback", self.name)
        tolerance = require_float(params, "tolerance_pct", self.name) / 100.0
        detection = PatternDetection()
        low = data["low"]
        index = data.index

        pivots = swing_lows(data, lookback, lookback)
        for first, second in zip(pivots, pivots[1:], strict=False):
            price_a = float(low.iloc[first])
            price_b = float(low.iloc[second])
            if price_a <= 0:
                continue
            relative = abs(price_a - price_b) / price_a
            if relative <= tolerance:
                level = (price_a + price_b) / 2.0
                detection.patterns.append(
                    PatternResult(
                        name=self.name,
                        pattern_type=self.pattern_type,
                        direction=PatternDirection.NEUTRAL,
                        strength=(
                            float(max(0.0, 100.0 * (1.0 - relative / tolerance)))
                            if tolerance
                            else 100.0
                        ),
                        confidence=0.6,
                        timestamp=index[second],
                        price_level=level,
                        metadata={
                            "first_index": first,
                            "second_index": second,
                            "first_price": price_a,
                            "second_price": price_b,
                            "relative_diff": relative,
                        },
                    )
                )
        return detection
