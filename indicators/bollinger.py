"""Bollinger-Bänder.

Berechnet Mittelband (SMA), oberes und unteres Band anhand der
Standardabweichung. Unabhängig von allen anderen Indikatoren.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from indicators.base import BaseIndicator, IndicatorOutput, require_float, require_int


class BollingerIndicator(BaseIndicator):
    """Bollinger-Bänder (oberes, mittleres, unteres Band)."""

    name = "bollinger"

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt ``period`` Kerzen für den gleitenden Durchschnitt."""
        return require_int(params, "period", self.name)

    def compute(self, data: pd.DataFrame, params: Mapping[str, Any]) -> IndicatorOutput:
        """Berechnet ``upper``, ``middle`` und ``lower``."""
        period = require_int(params, "period", self.name)
        std_dev = require_float(params, "std_dev", self.name)

        close = data["close"]
        middle = close.rolling(window=period, min_periods=period).mean()
        # Populations-Standardabweichung (ddof=0), wie bei Bollinger üblich.
        std = close.rolling(window=period, min_periods=period).std(ddof=0)

        output = IndicatorOutput(name=self.name)
        output.series["middle"] = middle
        output.series["upper"] = middle + std_dev * std
        output.series["lower"] = middle - std_dev * std
        return output
