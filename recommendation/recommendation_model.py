"""Recommendation Model – Stärke und Handlung samt No-Trade-Gates.

Bildet das Gesamtrating auf eine Empfehlungs**stärke** (VERY_HIGH … REJECT) und
eine Handlung (OPEN/WAIT/MONITOR/SKIP) ab. Die Stärke beschreibt ausschließlich
die **Qualität** der Entscheidung – **nicht** die Richtung (die steht getrennt in
``Direction``). Entscheidend sind die **Gates**: ein hoher Score/Rating allein
führt **nie** zu HIGH/VERY_HIGH; dafür müssen zusätzlich Konsens, Datenqualität
und ein nicht zu hohes Risiko stimmen („Kein Trade ist besser als ein schlechter
Trade"). Die Bewertungslogik ist unverändert – nur die Benennung ist fachlich
korrekt getrennt. Unabhängig von allen anderen Modellen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from recommendation.base import (
    BaseRecommendationModel,
    RecommendationContext,
    RecommendationModelOutput,
    RecommendationStrength,
    action_for_strength,
    cap_strength,
    is_neutral,
    require_float,
    strength_from_rating,
    strength_severity,
)

_THRESHOLD_KEYS = ("very_high_min", "high_min", "medium_min", "low_min")


class RecommendationModel(BaseRecommendationModel):
    """Stärke + Handlung aus Rating und No-Trade-Gates (Richtung getrennt)."""

    name = "recommendation_model"
    value_range = "Stärke (0=REJECT … 4=VERY_HIGH)"

    def compute(
        self, context: RecommendationContext, params: Mapping[str, Any]
    ) -> RecommendationModelOutput:
        """Bestimmt Empfehlungsstärke und Handlung inkl. Gates."""
        thresholds = {key: require_float(params, key, self.name) for key in _THRESHOLD_KEYS}
        max_risk_for_high = require_float(params, "max_overall_risk_for_high", self.name)
        min_consensus = require_float(params, "min_consensus_for_high", self.name)
        min_data_quality = require_float(params, "min_data_quality", self.name)

        rating = context.overall_rating
        strength = strength_from_rating(rating, thresholds)
        reasons = [f"Rating {rating:.0f} ⇒ {strength.value} (vor Gates)."]

        # No-Trade-Gates: verhindern, dass Score/Rating allein zu HIGH/VERY_HIGH führt.
        if is_neutral(context.direction):
            strength = cap_strength(strength, RecommendationStrength.LOW)
            reasons.append("Neutrale Richtung ⇒ höchstens LOW.")

        data_quality = context.factors["data_quality"].value
        if data_quality < min_data_quality:
            strength = cap_strength(strength, RecommendationStrength.LOW)
            reasons.append(f"Datenqualität {data_quality:.0f} < {min_data_quality:.0f} ⇒ LOW.")

        consensus = context.factors["consensus"].value
        if consensus < min_consensus:
            strength = cap_strength(strength, RecommendationStrength.MEDIUM)
            reasons.append(f"Konsens {consensus:.0f} < {min_consensus:.0f} ⇒ höchstens MEDIUM.")

        overall_risk = context.risk_result.overall_risk
        if overall_risk > max_risk_for_high:
            strength = cap_strength(strength, RecommendationStrength.MEDIUM)
            reasons.append(
                f"Risiko {overall_risk:.0f} > {max_risk_for_high:.0f} ⇒ höchstens MEDIUM."
            )

        action = action_for_strength(strength)
        return RecommendationModelOutput(
            name=self.name,
            value=float(strength_severity(strength)),
            reasons=reasons,
            details={"strength": strength, "action": action},
        )
