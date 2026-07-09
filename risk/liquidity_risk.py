"""Liquidity Risk – Risiko aus geringer Handelsliquidität.

Misst das durchschnittliche Handelsvolumen in Kontowährung (Preis × Volumen)
über ein Fenster. Geringe Liquidität ⇒ höheres Risiko. Unabhängig von allen
anderen Risk-Modellen.
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


class LiquidityRiskModel(BaseRiskModel):
    """Risiko aus dem durchschnittlichen Handelsvolumen (Preis × Volumen)."""

    name = "liquidity_risk"
    component = "liquidity"
    value_range = "0..100"

    def compute(self, context: RiskContext, params: Mapping[str, Any]) -> RiskModelOutput:
        """Berechnet das Liquiditätsrisiko (invers zum Handelsvolumen)."""
        window = require_int(params, "window", self.name)
        min_dollar_volume = require_float(params, "min_dollar_volume", self.name)
        good_dollar_volume = require_float(params, "good_dollar_volume", self.name)

        data = context.data
        columns = getattr(data, "columns", [])
        if data is None or "close" not in columns or "volume" not in columns or len(data) < 1:
            return RiskModelOutput(self.name, 50.0, ["Liquidität: unvollständige Daten (neutral)."])

        recent = data.tail(window)
        dollar_volume = float((recent["close"] * recent["volume"]).mean())
        # Invers skaliert: hohes Volumen ⇒ 0, niedriges ⇒ 100.
        value = scaled_risk(
            good_dollar_volume - dollar_volume, 0.0, good_dollar_volume - min_dollar_volume
        )
        return RiskModelOutput(
            name=self.name,
            value=value,
            reasons=[f"Liquidität: Ø Handelswert {dollar_volume:,.0f} pro Kerze."],
            details={"dollar_volume": dollar_volume},
        )
