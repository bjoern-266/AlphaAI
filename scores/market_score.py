"""Market Score – Marktumfeld der Hypothese (0..100).

Gewichtete Summe aus Marktkontext und Volumenqualität. Unabhängig von allen
anderen Score-Modellen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from scores.base import (
    BaseScoreModel,
    ScoreContext,
    ScoreModelOutput,
    validate_weights,
    weighted_sum,
)

_EXPECTED = ("market_context", "volume_quality")


class MarketScoreModel(BaseScoreModel):
    """Gewichteter Markt-Score (0..100)."""

    name = "market_score"
    value_range = "0..100"

    def compute(self, context: ScoreContext, params: Mapping[str, Any]) -> ScoreModelOutput:
        """Berechnet den Market Score aus Marktkontext und Volumenqualität."""
        weights = validate_weights(params, _EXPECTED, self.name)
        value = weighted_sum(weights, context.components)
        reasons = [
            f"{name}: {weights[name] * context.components[name].value:.0f}"
            f"/{weights[name] * 100:.0f}"
            for name in _EXPECTED
        ]
        return ScoreModelOutput(
            name=self.name,
            value=float(min(100.0, max(0.0, value))),
            reasons=reasons,
        )
