"""Explanation Model – erklärbare Gründe und Warnungen.

Sammelt die nachvollziehbaren Begründungen (aus Strategie, Score, Risiko,
Konsens, Markt-/Volumenqualität) und die Warnungen (erhöhte Risikokomponenten,
eingeschränkte Datenqualität, uneinige Strategien). Blackbox-Entscheidungen sind
nicht zulässig – jede Empfehlung ist so vollständig erklärbar. Unabhängig von
allen anderen Modellen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from recommendation.base import (
    BaseRecommendationModel,
    RecommendationContext,
    RecommendationModelOutput,
    require_float,
)


class ExplanationModel(BaseRecommendationModel):
    """Erzeugt Reasons und Warnings für die Transparenz."""

    name = "explanation_model"
    value_range = "n/a"

    def compute(
        self, context: RecommendationContext, params: Mapping[str, Any]
    ) -> RecommendationModelOutput:
        """Baut Reasons und Warnings aus dem gesamten Kontext."""
        good_market = require_float(params, "good_market_quality", self.name)
        good_volume = require_float(params, "good_volume_quality", self.name)
        weak_data_quality = require_float(params, "weak_data_quality", self.name)
        elevated_component = require_float(params, "elevated_component_risk", self.name)

        strategy = context.strategy_result
        score = context.score_result
        risk = context.risk_result

        reasons: list[str] = list(strategy.reasons)
        reasons.append(f"Score {score.total_score:.0f}/100")
        reasons.append(f"Risk {risk.risk_level.value.upper()}")
        if context.factors["consensus"].value >= 100.0:
            reasons.append("alle Strategien bestätigen die Richtung")
        elif context.factors["consensus"].value > 0.0:
            reasons.append(f"Konsens {context.factors['consensus'].value:.0f}/100")
        if context.factors["market_quality"].value >= good_market:
            reasons.append("Marktqualität bestätigt")
        volume_quality = float(score.component_scores.get("volume_quality", 0.0))
        if volume_quality >= good_volume:
            reasons.append("Volumen bestätigt")

        warnings: list[str] = []
        if context.factors["data_quality"].value < weak_data_quality:
            warnings.append("eingeschränkte Datenqualität")
        if context.factors["consensus"].value < 100.0:
            warnings.append("nicht alle Strategien einig")
        for name, value in risk.risk_components.items():
            if name != "data_quality" and value >= elevated_component:
                warnings.append(f"erhöhtes {name}-Risiko")

        return RecommendationModelOutput(
            name=self.name,
            reasons=reasons,
            warnings=warnings,
            details={"reasons": reasons, "warnings": warnings},
        )
