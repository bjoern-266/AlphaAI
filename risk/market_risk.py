"""Market Risk – Risiko aus einem ungünstigen Marktumfeld.

Leitet das Marktrisiko invers aus dem Market Score der Score Engine ab: ein
niedriger Market Score (schwaches Umfeld) bedeutet ein höheres Risiko.
Unabhängig von allen anderen Risk-Modellen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from risk.base import BaseRiskModel, RiskContext, RiskModelOutput, clamp_risk


class MarketRiskModel(BaseRiskModel):
    """Risiko aus dem Marktumfeld (invers zum Market Score)."""

    name = "market_risk"
    component = "market"
    value_range = "0..100"

    def compute(self, context: RiskContext, params: Mapping[str, Any]) -> RiskModelOutput:
        """Berechnet das Marktrisiko aus dem Market Score der Bewertung."""
        market_score = float(context.score_result.market_score)
        value = clamp_risk(100.0 - market_score)
        return RiskModelOutput(
            name=self.name,
            value=value,
            reasons=[f"Markt: Market Score {market_score:.0f}/100 (invers als Risiko)."],
            details={"market_score": market_score},
        )
