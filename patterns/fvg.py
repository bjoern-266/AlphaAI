"""Fair Value Gap (FVG) – Preis-Imbalance über drei Kerzen.

Erkennt bullische und bärische FVGs und deren Mitigations-Zustand
(fresh / partially_mitigated / mitigated). Unabhängig von allen anderen
Mustern.
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
    scaled_strength,
)

# Ein FVG von 5 % gilt als maximal ausgeprägt (Skalierung der Stärke).
_FULL_SCALE_RATIO = 0.05
# Vertrauen je Mitigations-Zustand (algorithmische Zuordnung, kein Parameter).
_CONFIDENCE_BY_STATE = {"fresh": 0.9, "partially_mitigated": 0.6, "mitigated": 0.3}


class FvgPattern(BasePattern):
    """Fair-Value-Gap-Detektor."""

    name = "fvg"
    pattern_type = PatternType.FAIR_VALUE_GAP

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt mindestens drei Kerzen."""
        return 3

    def detect(self, data: pd.DataFrame, params: Mapping[str, Any]) -> PatternDetection:
        """Erkennt alle FVGs oberhalb der Mindest-Gap-Größe."""
        min_gap_pct = require_float(params, "min_gap_pct", self.name)
        detection = PatternDetection()
        high = data["high"].to_numpy()
        low = data["low"].to_numpy()
        close = data["close"].to_numpy()
        index = data.index
        n = len(data)

        for i in range(1, n - 1):
            reference = close[i]
            if reference <= 0:
                continue

            bullish = low[i + 1] > high[i - 1]
            bearish = high[i + 1] < low[i - 1]
            if not bullish and not bearish:
                continue

            if bullish:
                bottom, top = high[i - 1], low[i + 1]
                direction = PatternDirection.BULLISH
            else:
                bottom, top = high[i + 1], low[i - 1]
                direction = PatternDirection.BEARISH

            gap_size = top - bottom
            gap_pct = gap_size / reference * 100.0
            if gap_pct < min_gap_pct:
                continue

            state = self._mitigation_state(data, i + 1, bottom, top, direction)
            detection.patterns.append(
                PatternResult(
                    name=self.name,
                    pattern_type=self.pattern_type,
                    direction=direction,
                    strength=scaled_strength(gap_size / reference, _FULL_SCALE_RATIO),
                    confidence=_CONFIDENCE_BY_STATE[state],
                    timestamp=index[i + 1],
                    price_level=(bottom + top) / 2.0,
                    metadata={
                        "candle_index": i + 1,
                        "gap_bottom": float(bottom),
                        "gap_top": float(top),
                        "gap_size": float(gap_size),
                        "gap_pct": float(gap_pct),
                        "state": state,
                        "fresh": state == "fresh",
                    },
                )
            )
        return detection

    @staticmethod
    def _mitigation_state(
        data: pd.DataFrame, formed_at: int, bottom: float, top: float, direction: PatternDirection
    ) -> str:
        """Bestimmt den Mitigations-Zustand aus der nachfolgenden Preisbewegung."""
        after = data.iloc[formed_at + 1 :]
        if after.empty:
            return "fresh"
        if direction is PatternDirection.BULLISH:
            min_low = float(after["low"].min())
            if min_low > top:
                return "fresh"
            if min_low <= bottom:
                return "mitigated"
            return "partially_mitigated"
        max_high = float(after["high"].max())
        if max_high < bottom:
            return "fresh"
        if max_high >= top:
            return "mitigated"
        return "partially_mitigated"
