"""Volatility Risk – Risiko aus der realisierten Volatilität.

Misst die Standardabweichung der Tagesrenditen über ein Fenster und skaliert
sie linear auf ein Risiko 0..100. Unabhängig von allen anderen Risk-Modellen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from risk.base import (
    BaseRiskModel,
    RiskContext,
    RiskModelOutput,
    require_float,
    require_int,
    scaled_risk,
)


class VolatilityRiskModel(BaseRiskModel):
    """Risiko aus der realisierten Volatilität (Tagesstandardabweichung)."""

    name = "volatility_risk"
    component = "volatility"
    value_range = "0..100"

    def compute(self, context: RiskContext, params: Mapping[str, Any]) -> RiskModelOutput:
        """Berechnet das Volatilitätsrisiko."""
        window = require_int(params, "window", self.name)
        low = require_float(params, "vol_low_pct", self.name)
        high = require_float(params, "vol_high_pct", self.name)

        data = context.data
        if data is None or "close" not in getattr(data, "columns", []) or len(data) < 2:
            return RiskModelOutput(
                self.name, 50.0, ["Volatilität: unvollständige Daten (neutral)."]
            )
        returns = data["close"].pct_change().dropna().tail(window)
        if returns.empty:
            return RiskModelOutput(self.name, 50.0, ["Volatilität: zu wenig Historie (neutral)."])
        vol_pct = float(returns.std() * 100.0)
        value = scaled_risk(vol_pct, low, high)
        return RiskModelOutput(
            name=self.name,
            value=value,
            reasons=[f"Volatilität: {vol_pct:.2f} % (Tagesstandardabweichung)."],
            details={"volatility_pct": vol_pct},
        )
