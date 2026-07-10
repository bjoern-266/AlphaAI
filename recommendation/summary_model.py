"""Summary Model – menschenlesbare Kurzfassung der Empfehlung.

Erzeugt den beschreibenden Kern der Zusammenfassung (Symbol, Richtung, Rating,
Risiko, Konsens). Die endgültige Stufe/Handlung stellt die Engine voran, sobald
das Recommendation Model sie bestimmt hat. Unabhängig von allen anderen Modellen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from recommendation.base import (
    BaseRecommendationModel,
    RecommendationContext,
    RecommendationModelOutput,
)


class SummaryModel(BaseRecommendationModel):
    """Erzeugt den beschreibenden Kern der Zusammenfassung."""

    name = "summary_model"
    value_range = "n/a"

    def compute(
        self, context: RecommendationContext, params: Mapping[str, Any]
    ) -> RecommendationModelOutput:
        """Baut den Zusammenfassungs-Text (ohne die finale Stufe)."""
        symbol = context.symbol or "Symbol"
        body = (
            f"{symbol} Richtung {context.trade_direction.value.upper()}, Rating "
            f"{context.overall_rating:.0f}/100, Risiko "
            f"{context.risk_result.risk_level.value}, Konsens "
            f"{context.factors['consensus'].value:.0f}/100, Confidence "
            f"{context.base_confidence:.2f}."
        )
        return RecommendationModelOutput(
            name=self.name, value=context.overall_rating, details={"summary": body}
        )
