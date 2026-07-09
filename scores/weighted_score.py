"""Weighted Score – Gesamtscore als gewichtete Summe aller Komponenten.

Kombiniert alle acht Komponenten mit den in der Konfiguration hinterlegten
Gewichten zu einem transparenten Gesamtscore (0..100). Unabhängig von allen
anderen Score-Modellen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from scores.base import (
    COMPONENT_NAMES,
    BaseScoreModel,
    ScoreContext,
    ScoreModelOutput,
    validate_weights,
)


class WeightedScoreModel(BaseScoreModel):
    """Gewichteter Gesamtscore über alle acht Komponenten."""

    name = "weighted_score"
    value_range = "0..100"

    def compute(self, context: ScoreContext, params: Mapping[str, Any]) -> ScoreModelOutput:
        """Berechnet den Gesamtscore und die Beiträge je Komponente."""
        weights = validate_weights(params, COMPONENT_NAMES, self.name)

        total = 0.0
        reasons: list[str] = []
        details: dict[str, Any] = {}
        for name in COMPONENT_NAMES:
            component = context.components[name]
            contribution = weights[name] * component.value
            maximum = weights[name] * 100.0
            total += contribution
            details[name] = {"contribution": contribution, "max": maximum, "value": component.value}
            reasons.append(f"{name}: {contribution:.0f}/{maximum:.0f}")

        return ScoreModelOutput(
            name=self.name,
            value=float(min(100.0, max(0.0, total))),
            reasons=reasons,
            details=details,
        )
