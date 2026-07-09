"""Recommendation Model – Stufe und Handlung samt No-Trade-Gates.

Bildet das Gesamtrating auf eine Empfehlungsstufe (STRONG_BUY … AVOID) und eine
Handlung (OPEN/WAIT/MONITOR/SKIP) ab. Entscheidend sind die **Gates**: Ein hoher
Score/Rating allein führt **nie** zu BUY/STRONG_BUY – dafür müssen zusätzlich
Konsens, Datenqualität und ein nicht zu hohes Risiko stimmen. So bleibt „Kein
Trade ist besser als ein schlechter Trade" gewahrt. Unabhängig von allen anderen
Modellen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from recommendation.base import (
    BaseRecommendationModel,
    RecommendationContext,
    RecommendationLevel,
    RecommendationModelOutput,
    action_for_level,
    cap_level,
    is_neutral,
    level_from_rating,
    level_severity,
    require_float,
)

_THRESHOLD_KEYS = ("strong_buy_min", "buy_min", "watch_min", "wait_min")


class RecommendationModel(BaseRecommendationModel):
    """Stufe + Handlung aus Rating und No-Trade-Gates."""

    name = "recommendation_model"
    value_range = "Stufe (0=AVOID … 4=STRONG_BUY)"

    def compute(
        self, context: RecommendationContext, params: Mapping[str, Any]
    ) -> RecommendationModelOutput:
        """Bestimmt Empfehlungsstufe und Handlung inkl. Gates."""
        thresholds = {key: require_float(params, key, self.name) for key in _THRESHOLD_KEYS}
        max_risk_for_buy = require_float(params, "max_overall_risk_for_buy", self.name)
        min_consensus = require_float(params, "min_consensus_for_buy", self.name)
        min_data_quality = require_float(params, "min_data_quality", self.name)

        rating = context.overall_rating
        level = level_from_rating(rating, thresholds)
        reasons = [f"Rating {rating:.0f} ⇒ {level.value} (vor Gates)."]

        # No-Trade-Gates: verhindern, dass Score/Rating allein zu BUY führt.
        if is_neutral(context.direction):
            level = cap_level(level, RecommendationLevel.WAIT)
            reasons.append("Neutrale Richtung ⇒ höchstens WAIT.")

        data_quality = context.factors["data_quality"].value
        if data_quality < min_data_quality:
            level = cap_level(level, RecommendationLevel.WAIT)
            reasons.append(f"Datenqualität {data_quality:.0f} < {min_data_quality:.0f} ⇒ WAIT.")

        consensus = context.factors["consensus"].value
        if consensus < min_consensus:
            level = cap_level(level, RecommendationLevel.WATCH)
            reasons.append(
                f"Konsens {consensus:.0f} < {min_consensus:.0f} ⇒ kein BUY (höchstens WATCH)."
            )

        overall_risk = context.risk_result.overall_risk
        if overall_risk > max_risk_for_buy:
            level = cap_level(level, RecommendationLevel.WATCH)
            reasons.append(
                f"Risiko {overall_risk:.0f} > {max_risk_for_buy:.0f} ⇒ kein BUY (höchstens WATCH)."
            )

        action = action_for_level(level)
        return RecommendationModelOutput(
            name=self.name,
            value=float(level_severity(level)),
            reasons=reasons,
            details={"level": level, "action": action},
        )
