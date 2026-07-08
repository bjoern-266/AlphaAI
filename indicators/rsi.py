"""Relative Strength Index (RSI) nach Wilder.

Misst die Geschwindigkeit und Richtung von Kursbewegungen. Unabhängig von
allen anderen Indikatoren.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from indicators.base import BaseIndicator, IndicatorOutput, require_int, safe_divide


class RsiIndicator(BaseIndicator):
    """Relative Strength Index (Wilder-Glättung)."""

    name = "rsi"

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt ``period + 1`` Kerzen (für die erste Differenz)."""
        return require_int(params, "period", self.name) + 1

    def compute(self, data: pd.DataFrame, params: Mapping[str, Any]) -> IndicatorOutput:
        """Berechnet ``rsi_<period>`` im Bereich 0..100."""
        period = require_int(params, "period", self.name)
        close = data["close"]
        delta = close.diff()
        gain = delta.clip(lower=0.0)
        loss = -delta.clip(upper=0.0)

        avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

        rs = safe_divide(avg_gain, avg_loss)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        # Bei Verlust 0 (Division durch Null) ist der Markt rein steigend -> RSI 100.
        rsi = rsi.mask((avg_loss == 0) & (avg_gain > 0), 100.0)

        output = IndicatorOutput(name=self.name)
        output.series[f"rsi_{period}"] = rsi
        return output
