"""Decision Model – legt das erklärbare Gesamtrating der Empfehlung offen.

Das Gesamtrating (0..100) ist die gewichtete Kombination der sechs
Entscheidungsfaktoren (Strategie, Score, Risiko, Konsens, Marktqualität,
Datenqualität), die die Engine vorab berechnet. Dieses Modell macht das Rating
und die Faktor-Begründungen transparent verfügbar. Unabhängig von allen anderen
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


class DecisionModel(BaseRecommendationModel):
    """Stellt das Gesamtrating und die Faktor-Begründungen bereit."""

    name = "decision_model"
    value_range = "0..100"

    def compute(
        self, context: RecommendationContext, params: Mapping[str, Any]
    ) -> RecommendationModelOutput:
        """Liefert das vorab berechnete Gesamtrating samt Faktor-Begründungen."""
        rating = context.overall_rating
        reasons = [factor.reason for factor in context.factors.values()]
        return RecommendationModelOutput(
            name=self.name,
            value=rating,
            reasons=reasons,
            details={
                "rating": rating,
                "factors": {name: f.value for name, f in context.factors.items()},
            },
        )
