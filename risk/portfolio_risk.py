"""Portfolio Risk – Risiko aus dem Gesamtengagement des Depots.

Bewertet das aktuelle Gesamtengagement (Summe der offenen Positionswerte) im
Verhältnis zum Depot. Ohne offene Positionen ist das Risiko 0. **Vorbereitet**
für den späteren Portfolio-Betrieb: die Engine reicht bereits offene Positionen
durch, sodass dieses Modell voll implementiert werden kann, sobald sie geführt
werden. Unabhängig von allen anderen Risk-Modellen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from risk.base import BaseRiskModel, RiskContext, RiskModelOutput, require_float, scaled_risk


class PortfolioRiskModel(BaseRiskModel):
    """Risiko aus dem Gesamtengagement offener Positionen (vorbereitet)."""

    name = "portfolio_risk"
    component = "portfolio_exposure"
    value_range = "0..100"

    def compute(self, context: RiskContext, params: Mapping[str, Any]) -> RiskModelOutput:
        """Berechnet das Portfolio-Exposure-Risiko."""
        max_exposure_ratio = require_float(params, "max_exposure_ratio", self.name)
        capital = context.account.capital
        positions = list(context.open_positions)
        if capital <= 0:
            return RiskModelOutput(self.name, 50.0, ["Portfolio: ungültige Depotgröße (neutral)."])
        exposure = sum(p.value for p in positions)
        ratio = exposure / capital
        value = scaled_risk(ratio, 0.0, max_exposure_ratio)
        return RiskModelOutput(
            name=self.name,
            value=value,
            reasons=[
                f"Portfolio: Engagement {exposure:,.0f} = {ratio * 100:.0f} % des Depots "
                f"({len(positions)} Position(en))."
            ],
            details={"exposure": exposure, "exposure_ratio": ratio},
        )
