"""Quality Score – Datengüte der Bewertung (0..100).

Gewichtete Summe der Qualitätskomponenten (Indikatorqualität, Musterkonfidenz,
Datenqualität). Unabhängig von allen anderen Score-Modellen.
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

_EXPECTED = ("indicator_quality", "pattern_confidence", "data_quality")


class QualityScoreModel(BaseScoreModel):
    """Gewichteter Qualitäts-Score (0..100)."""

    name = "quality_score"
    value_range = "0..100"

    def compute(self, context: ScoreContext, params: Mapping[str, Any]) -> ScoreModelOutput:
        """Berechnet den Quality Score aus den Qualitätskomponenten."""
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
