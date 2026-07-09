"""Execution Risk – Risiko aus Ausführungskosten (Spread + Slippage).

Schätzt die Roundtrip-Ausführungskosten (Spread plus zweimalige Slippage) als
Prozentsatz des Preises und skaliert sie auf ein Risiko 0..100. Füllt die
Komponente ``spread``. Unabhängig von allen anderen Risk-Modellen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from risk.base import (
    BaseRiskModel,
    RiskContext,
    RiskModelOutput,
    require_float,
    scaled_risk,
)


class ExecutionRiskModel(BaseRiskModel):
    """Risiko aus Ausführungskosten (Spread + Slippage, Roundtrip)."""

    name = "execution_risk"
    component = "spread"
    value_range = "0..100"

    def compute(self, context: RiskContext, params: Mapping[str, Any]) -> RiskModelOutput:
        """Berechnet das Ausführungs-/Spread-Risiko."""
        spread_bps = require_float(params, "spread_bps", self.name)
        slippage_bps = require_float(params, "slippage_bps", self.name)
        cost_low_pct = require_float(params, "cost_low_pct", self.name)
        cost_high_pct = require_float(params, "cost_high_pct", self.name)

        # Roundtrip-Kosten in Prozent: Spread + 2 × Slippage (Ein- und Ausstieg).
        cost_pct = (spread_bps + 2.0 * slippage_bps) / 100.0
        value = scaled_risk(cost_pct, cost_low_pct, cost_high_pct)
        return RiskModelOutput(
            name=self.name,
            value=value,
            reasons=[f"Spread/Ausführung: Roundtrip-Kosten ≈ {cost_pct:.3f} % des Preises."],
            details={"cost_pct": cost_pct},
        )
