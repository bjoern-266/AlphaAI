"""Volume Profile.

Verteilt das gehandelte Volumen auf Preis-Bänder (Bins) über die Spanne des
Datenfensters und ermittelt den Point of Control (POC) – das Preisniveau mit
dem höchsten Volumen. Unabhängig von allen anderen Indikatoren.

Im Gegensatz zu den übrigen Indikatoren ist das Ergebnis keine Zeitreihe,
sondern eine Verteilung über Preisniveaus. Es wird als Serie (Index =
Bin-Mittelpunkt, Wert = Volumen) unter ``volume_profile`` abgelegt; der POC
steht in ``extra['poc']``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from indicators.base import BaseIndicator, IndicatorOutput, require_int


class VolumeProfileIndicator(BaseIndicator):
    """Volumenverteilung über Preis-Bänder inkl. Point of Control."""

    name = "volume_profile"
    requires_volume = True

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt mindestens eine Kerze."""
        return 1

    def compute(self, data: pd.DataFrame, params: Mapping[str, Any]) -> IndicatorOutput:
        """Berechnet die Volumenverteilung und den Point of Control."""
        bins = require_int(params, "bins", self.name)
        close = data["close"]
        volume = data["volume"]
        output = IndicatorOutput(name=self.name)

        price_min = float(close.min())
        price_max = float(close.max())
        if price_min == price_max:
            # Alle Kurse identisch: eine einzige Preisstufe.
            profile = pd.Series([float(volume.sum())], index=[price_min])
            output.series["volume_profile"] = profile
            output.extra["poc"] = price_min
            output.warnings.append("Volume Profile: konstante Kurse, nur ein Preisniveau.")
            return output

        edges = pd.interval_range(start=price_min, end=price_max, periods=bins)
        buckets = pd.cut(close, bins=bins, include_lowest=True)
        grouped = volume.groupby(buckets, observed=False).sum()
        midpoints = [interval.mid for interval in edges]
        profile = pd.Series(grouped.to_numpy(), index=midpoints)

        output.series["volume_profile"] = profile
        output.extra["poc"] = float(profile.idxmax())
        return output
