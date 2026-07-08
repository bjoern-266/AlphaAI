"""Change of Character (CHoCH) – Trendwechsel.

Ein CHoCH ist ein Struktur-Bruch gegen den bestehenden Trend (erster Bruch,
der die Struktur umkehrt). Nutzt den gemeinsamen Struktur-Helper und ist damit
unabhängig von den übrigen Mustern.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from patterns.base import (
    BasePattern,
    PatternDetection,
    PatternResult,
    PatternType,
    detect_structure_breaks,
    require_int,
    scaled_strength,
)

_FULL_SCALE_RATIO = 0.02
_CONFIDENCE = 0.7


class ChochPattern(BasePattern):
    """Change-of-Character-Detektor."""

    name = "choch"
    pattern_type = PatternType.STRUCTURE_BREAK

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt genug Kerzen, um Swings zu bestätigen."""
        return 2 * require_int(params, "swing_lookback", self.name) + 1

    def detect(self, data: pd.DataFrame, params: Mapping[str, Any]) -> PatternDetection:
        """Erkennt alle CHoCH-Ereignisse (Trendwechsel)."""
        lookback = require_int(params, "swing_lookback", self.name)
        detection = PatternDetection()
        close = data["close"].to_numpy()
        for event in detect_structure_breaks(data, lookback):
            if event.kind != "choch":
                continue
            distance = abs(close[event.index] - event.level)
            ratio = distance / event.level if event.level else 0.0
            detection.patterns.append(
                PatternResult(
                    name=self.name,
                    pattern_type=self.pattern_type,
                    direction=event.direction,
                    strength=scaled_strength(ratio, _FULL_SCALE_RATIO),
                    confidence=_CONFIDENCE,
                    timestamp=event.timestamp,
                    price_level=event.level,
                    metadata={"break_level": event.level, "candle_index": event.index},
                )
            )
        return detection
