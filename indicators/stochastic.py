"""Stochastik-Oszillator.

Berechnet die geglättete %K- und die %D-Linie im Bereich 0..100. Unabhängig
von allen anderen Indikatoren.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from indicators.base import BaseIndicator, IndicatorOutput, require_int, safe_divide


class StochasticIndicator(BaseIndicator):
    """Stochastik-Oszillator (%K und %D)."""

    name = "stochastic"

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt ``k_period + smooth_k + d_period`` Kerzen."""
        k_period = require_int(params, "k_period", self.name)
        d_period = require_int(params, "d_period", self.name)
        smooth_k = require_int(params, "smooth_k", self.name)
        return k_period + smooth_k + d_period

    def compute(self, data: pd.DataFrame, params: Mapping[str, Any]) -> IndicatorOutput:
        """Berechnet ``percent_k`` und ``percent_d``."""
        k_period = require_int(params, "k_period", self.name)
        d_period = require_int(params, "d_period", self.name)
        smooth_k = require_int(params, "smooth_k", self.name)

        low_min = data["low"].rolling(window=k_period, min_periods=k_period).min()
        high_max = data["high"].rolling(window=k_period, min_periods=k_period).max()
        raw_k = 100.0 * safe_divide(data["close"] - low_min, high_max - low_min)
        percent_k = raw_k.rolling(window=smooth_k, min_periods=smooth_k).mean()
        percent_d = percent_k.rolling(window=d_period, min_periods=d_period).mean()

        output = IndicatorOutput(name=self.name)
        output.series["percent_k"] = percent_k
        output.series["percent_d"] = percent_d
        return output
