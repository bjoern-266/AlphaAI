"""Average Directional Index (ADX) nach Wilder.

Misst die Trendstärke (0..100) und liefert zusätzlich die Richtungsindizes
+DI und -DI. Unabhängig von allen anderen Indikatoren (die True Range stammt
aus dem gemeinsamen Hilfsmittel in ``indicators.base``).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from indicators.base import (
    BaseIndicator,
    IndicatorOutput,
    require_int,
    safe_divide,
    true_range,
)


class AdxIndicator(BaseIndicator):
    """Average Directional Index mit +DI und -DI."""

    name = "adx"

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt etwa ``2 * period`` Kerzen (Doppelglättung)."""
        return 2 * require_int(params, "period", self.name)

    def compute(self, data: pd.DataFrame, params: Mapping[str, Any]) -> IndicatorOutput:
        """Berechnet ``adx``, ``plus_di`` und ``minus_di``."""
        period = require_int(params, "period", self.name)
        high = data["high"]
        low = data["low"]

        up_move = high.diff()
        down_move = -low.diff()
        plus_dm = pd.Series(
            np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=data.index
        )
        minus_dm = pd.Series(
            np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=data.index
        )

        alpha = 1.0 / period
        atr = true_range(data).ewm(alpha=alpha, min_periods=period, adjust=False).mean()
        plus_di = 100.0 * safe_divide(
            plus_dm.ewm(alpha=alpha, min_periods=period, adjust=False).mean(), atr
        )
        minus_di = 100.0 * safe_divide(
            minus_dm.ewm(alpha=alpha, min_periods=period, adjust=False).mean(), atr
        )

        di_sum = plus_di + minus_di
        dx = 100.0 * safe_divide((plus_di - minus_di).abs(), di_sum)
        adx = dx.ewm(alpha=alpha, min_periods=period, adjust=False).mean()

        output = IndicatorOutput(name=self.name)
        output.series["adx"] = adx
        output.series["plus_di"] = plus_di
        output.series["minus_di"] = minus_di
        return output
