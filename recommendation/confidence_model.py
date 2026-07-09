"""Confidence Model – Vertrauen (0..1) in die Empfehlung.

Stellt die von der Engine vorab berechnete Confidence bereit. Sie folgt aus dem
Strategie-Vertrauen, dem Konsens der Hypothesen, dem (invertierten) Risiko und
der Datenqualität – nicht aus dem Score allein. Unabhängig von allen anderen
Modellen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from recommendation.base import (
    BaseRecommendationModel,
    RecommendationContext,
    RecommendationModelOutput,
)


class ConfidenceModel(BaseRecommendationModel):
    """Liefert die Confidence 0..1 der Empfehlung."""

    name = "confidence_model"
    value_range = "0..1"

    def compute(
        self, context: RecommendationContext, params: Mapping[str, Any]
    ) -> RecommendationModelOutput:
        """Gibt die vorab berechnete Confidence samt Begründung zurück."""
        confidence = context.base_confidence
        return RecommendationModelOutput(
            name=self.name,
            value=confidence,
            reasons=[
                f"Confidence {confidence:.2f} aus Strategie-Vertrauen, Konsens, "
                f"Risiko und Datenqualität."
            ],
            details={"confidence": confidence},
        )
