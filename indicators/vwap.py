"""Volume Weighted Average Price (VWAP).

Kumulativer volumengewichteter Durchschnittskurs über das übergebene
Datenfenster. Unabhängig von allen anderen Indikatoren.

Hinweis: Diese Umsetzung berechnet den VWAP kumulativ über das gesamte
Fenster. Ein sitzungsweiser Reset (typisch für Intraday-VWAP) ist im Rahmen
der Multi-Timeframe-Erweiterung vorgesehen und hier bewusst nicht enthalten.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from indicators.base import BaseIndicator, IndicatorOutput, safe_divide


class VwapIndicator(BaseIndicator):
    """Kumulativer volumengewichteter Durchschnittskurs."""

    name = "vwap"
    requires_volume = True

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt mindestens eine Kerze."""
        return 1

    def compute(self, data: pd.DataFrame, params: Mapping[str, Any]) -> IndicatorOutput:
        """Berechnet ``vwap`` aus typischem Preis und Volumen."""
        typical_price = (data["high"] + data["low"] + data["close"]) / 3.0
        volume = data["volume"]
        cumulative_pv = (typical_price * volume).cumsum()
        cumulative_volume = volume.cumsum()
        vwap = safe_divide(cumulative_pv, cumulative_volume)

        output = IndicatorOutput(name=self.name)
        output.series["vwap"] = vwap
        return output
