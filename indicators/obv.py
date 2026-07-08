"""On-Balance Volume (OBV).

Kumuliert das Volumen richtungsabhängig (Aufwärtstag addiert, Abwärtstag
subtrahiert). Unabhängig von allen anderen Indikatoren.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from indicators.base import BaseIndicator, IndicatorOutput


class ObvIndicator(BaseIndicator):
    """On-Balance Volume."""

    name = "obv"
    requires_volume = True

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt mindestens zwei Kerzen (für die Richtungsbestimmung)."""
        return 2

    def compute(self, data: pd.DataFrame, params: Mapping[str, Any]) -> IndicatorOutput:
        """Berechnet die kumulierte ``obv``-Reihe."""
        close = data["close"]
        volume = data["volume"]
        direction = np.sign(close.diff().fillna(0.0))
        obv = (direction * volume).cumsum()

        output = IndicatorOutput(name=self.name)
        output.series["obv"] = obv
        return output
