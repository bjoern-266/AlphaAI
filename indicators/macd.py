"""Moving Average Convergence Divergence (MACD).

Berechnet MACD-Linie, Signallinie und Histogramm. Unabhängig von allen
anderen Indikatoren (die enthaltenen EMAs werden lokal berechnet, nicht vom
EMA-Indikator übernommen).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from indicators.base import BaseIndicator, IndicatorOutput, require_int


class MacdIndicator(BaseIndicator):
    """MACD mit Linie, Signal und Histogramm."""

    name = "macd"

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt ``slow + signal`` Kerzen für eine stabile Signallinie."""
        slow = require_int(params, "slow", self.name)
        signal = require_int(params, "signal", self.name)
        return slow + signal

    def compute(self, data: pd.DataFrame, params: Mapping[str, Any]) -> IndicatorOutput:
        """Berechnet ``macd``, ``signal`` und ``histogram``."""
        fast = require_int(params, "fast", self.name)
        slow = require_int(params, "slow", self.name)
        signal_period = require_int(params, "signal", self.name)

        close = data["close"]
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line

        output = IndicatorOutput(name=self.name)
        output.series["macd"] = macd_line
        output.series["signal"] = signal_line
        output.series["histogram"] = histogram
        return output
