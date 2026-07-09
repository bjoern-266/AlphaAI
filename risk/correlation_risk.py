"""Correlation Risk – Risiko aus Korrelation mit offenen Positionen.

Bewertet, wie stark ein neuer Trade mit bereits offenen Positionen korreliert
(gleiche Korrelationsgruppe, z. B. Sektor/Index). Ohne offene Positionen ist
das Risiko 0. **Vorbereitet** für den späteren Portfolio-Betrieb; unabhängig
von allen anderen Risk-Modellen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from risk.base import BaseRiskModel, RiskContext, RiskModelOutput, clamp_risk, require_float


class CorrelationRiskModel(BaseRiskModel):
    """Risiko aus Korrelation mit bereits offenen Positionen (vorbereitet)."""

    name = "correlation_risk"
    component = "correlation"
    value_range = "0..100"

    def compute(self, context: RiskContext, params: Mapping[str, Any]) -> RiskModelOutput:
        """Berechnet das Korrelationsrisiko aus den offenen Positionen."""
        risk_per_correlated = require_float(params, "risk_per_correlated", self.name)
        positions = list(context.open_positions)
        if not positions:
            return RiskModelOutput(
                self.name, 0.0, ["Korrelation: keine offenen Positionen (kein Risiko)."]
            )
        # Ohne bekannte Gruppe des neuen Symbols werden alle offenen Positionen
        # als potenziell korreliert gewertet (konservativ, Portfolio-Vorbereitung).
        correlated = len(positions)
        value = clamp_risk(risk_per_correlated * correlated)
        return RiskModelOutput(
            name=self.name,
            value=value,
            reasons=[f"Korrelation: {correlated} offene Position(en) potenziell korreliert."],
            details={"correlated_positions": correlated},
        )
