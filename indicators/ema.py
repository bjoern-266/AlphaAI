"""Exponentieller gleitender Durchschnitt (EMA).

Berechnet für jede konfigurierte Periode einen EMA auf Basis der
Schlusskurse. Unabhängig von allen anderen Indikatoren.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from indicators.base import BaseIndicator, IndicatorOutput, require_int_list


class EmaIndicator(BaseIndicator):
    """Exponentieller gleitender Durchschnitt für mehrere Perioden."""

    name = "ema"

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt so viele Kerzen wie die kleinste konfigurierte Periode.

        Der Indikator berechnet mehrere Perioden gemeinsam. Perioden, für die
        noch nicht genug Historie vorliegt, liefern über ``min_periods`` ehrlich
        ``NaN`` (statt den gesamten Indikator zu blockieren).
        """
        return min(require_int_list(params, "periods", self.name))

    def compute(self, data: pd.DataFrame, params: Mapping[str, Any]) -> IndicatorOutput:
        """Berechnet je Periode ``ema_<periode>`` aus den Schlusskursen."""
        periods = require_int_list(params, "periods", self.name)
        close = data["close"]
        output = IndicatorOutput(name=self.name)
        for period in periods:
            output.series[f"ema_{period}"] = close.ewm(
                span=period, adjust=False, min_periods=period
            ).mean()
        return output
