"""Relatives Volumen (Relative Volume, RVOL).

Setzt das aktuelle Volumen ins Verhältnis zum durchschnittlichen Volumen der
letzten ``period`` Kerzen. Unabhängig von allen anderen Indikatoren.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from indicators.base import BaseIndicator, IndicatorOutput, require_int, safe_divide


class RelativeVolumeIndicator(BaseIndicator):
    """Relatives Volumen gegenüber dem gleitenden Durchschnittsvolumen."""

    name = "relative_volume"
    requires_volume = True

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt ``period`` Kerzen für den Durchschnitt."""
        return require_int(params, "period", self.name)

    def compute(self, data: pd.DataFrame, params: Mapping[str, Any]) -> IndicatorOutput:
        """Berechnet ``relative_volume`` (1.0 = Durchschnitt)."""
        period = require_int(params, "period", self.name)
        volume = data["volume"]
        average = volume.rolling(window=period, min_periods=period).mean()
        rvol = safe_divide(volume, average)

        output = IndicatorOutput(name=self.name)
        output.series["relative_volume"] = rvol
        return output
