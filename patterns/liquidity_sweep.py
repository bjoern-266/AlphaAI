"""Liquidity Sweep – kurzes Durchstoßen eines Swings mit Rückkehr.

Ein bärischer Sweep durchsticht ein Swing High (nimmt Kauf-Liquidität) und
schließt darunter zurück; ein bullischer Sweep durchsticht ein Swing Low und
schließt darüber. Unabhängig von allen anderen Mustern.
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
    scaled_strength,
    swing_highs,
    swing_lows,
)

# Eine Durchdringung von 1 % gilt als maximal ausgeprägt.
_FULL_SCALE_RATIO = 0.01
_CONFIDENCE = 0.65


class LiquiditySweepPattern(BasePattern):
    """Detektor für Liquidity Sweeps an Swing-Hochs/-Tiefs."""

    name = "liquidity_sweep"
    pattern_type = PatternType.LIQUIDITY

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt genug Kerzen für Swings plus Folgebewegung."""
        return 2 * require_int(params, "swing_lookback", self.name) + 2

    def detect(self, data: pd.DataFrame, params: Mapping[str, Any]) -> PatternDetection:
        """Erkennt bärische (Hochs) und bullische (Tiefs) Sweeps."""
        lookback = require_int(params, "swing_lookback", self.name)
        penetration = require_float(params, "penetration_pct", self.name) / 100.0
        detection = PatternDetection()

        self._sweep_side(
            data,
            swing_highs(data, lookback, lookback),
            lookback,
            penetration,
            PatternDirection.BEARISH,
            detection,
        )
        self._sweep_side(
            data,
            swing_lows(data, lookback, lookback),
            lookback,
            penetration,
            PatternDirection.BULLISH,
            detection,
        )
        detection.patterns.sort(key=lambda p: p.metadata["candle_index"])
        return detection

    def _sweep_side(
        self,
        data: pd.DataFrame,
        pivots: list[int],
        lookback: int,
        penetration: float,
        direction: PatternDirection,
        detection: PatternDetection,
    ) -> None:
        """Sucht je Pivot die erste Kerze, die das Level sweept."""
        high = data["high"].to_numpy()
        low = data["low"].to_numpy()
        close = data["close"].to_numpy()
        index = data.index
        n = len(data)

        for pivot in pivots:
            level = high[pivot] if direction is PatternDirection.BEARISH else low[pivot]
            if level <= 0:
                continue
            for i in range(pivot + lookback + 1, n):
                if direction is PatternDirection.BEARISH:
                    swept = high[i] > level * (1.0 + penetration) and close[i] < level
                    depth = (high[i] - level) / level
                else:
                    swept = low[i] < level * (1.0 - penetration) and close[i] > level
                    depth = (level - low[i]) / level
                if swept:
                    detection.patterns.append(
                        PatternResult(
                            name=self.name,
                            pattern_type=self.pattern_type,
                            direction=direction,
                            strength=scaled_strength(depth, _FULL_SCALE_RATIO),
                            confidence=_CONFIDENCE,
                            timestamp=index[i],
                            price_level=float(level),
                            metadata={
                                "candle_index": i,
                                "pivot_index": pivot,
                                "swept_level": float(level),
                                "penetration_depth": float(depth),
                            },
                        )
                    )
                    break
