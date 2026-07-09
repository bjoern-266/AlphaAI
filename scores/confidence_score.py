"""Confidence Score – Vertrauen in die Hypothese (0..1).

Kombiniert die Strategie-Confidence, die Muster-Confidence und den Konsens der
Hypothesen zu einem Vertrauenswert. Unabhängig von allen anderen Score-Modellen
(der Konsens wird über den gemeinsamen Helfer berechnet, nicht über das
Consensus-Modell).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from scores.base import (
    BaseScoreModel,
    ScoreContext,
    ScoreModelOutput,
    consensus_fraction,
    validate_weights,
)

_EXPECTED = ("strategy_confidence", "pattern_confidence", "consensus")


class ConfidenceScoreModel(BaseScoreModel):
    """Gewichteter Vertrauenswert (0..1)."""

    name = "confidence_score"
    value_range = "0..1"

    def compute(self, context: ScoreContext, params: Mapping[str, Any]) -> ScoreModelOutput:
        """Berechnet den Confidence Score aus drei Quellen."""
        weights = validate_weights(params, _EXPECTED, self.name)

        strategy_conf = float(context.strategy_result.confidence)
        pattern_conf = context.components["pattern_confidence"].value / 100.0
        consensus = consensus_fraction(context.strategy_result, context.hypotheses)

        value = (
            weights["strategy_confidence"] * strategy_conf
            + weights["pattern_confidence"] * pattern_conf
            + weights["consensus"] * consensus
        )
        reasons = [
            f"strategy_confidence: {strategy_conf:.2f}",
            f"pattern_confidence: {pattern_conf:.2f}",
            f"consensus: {consensus:.2f}",
        ]
        return ScoreModelOutput(
            name=self.name,
            value=float(min(1.0, max(0.0, value))),
            reasons=reasons,
        )
