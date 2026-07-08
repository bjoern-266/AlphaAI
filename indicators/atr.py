"""Average True Range (ATR) nach Wilder.

Misst die Volatilität über die True Range. Unabhängig von allen anderen
Indikatoren (die True-Range-Hilfsfunktion liegt in ``indicators.base``).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from indicators.base import BaseIndicator, IndicatorOutput, require_int, true_range


class AtrIndicator(BaseIndicator):
    """Average True Range (Wilder-Glättung)."""

    name = "atr"

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt ``period + 1`` Kerzen (True Range nutzt den Vorkurs)."""
        return require_int(params, "period", self.name) + 1

    def compute(self, data: pd.DataFrame, params: Mapping[str, Any]) -> IndicatorOutput:
        """Berechnet ``atr_<period>``."""
        period = require_int(params, "period", self.name)
        tr = true_range(data)
        atr = tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

        output = IndicatorOutput(name=self.name)
        output.series[f"atr_{period}"] = atr
        return output
