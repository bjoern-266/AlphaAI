"""Consensus Score – Übereinstimmung der Hypothesen-Richtungen (0..100).

Misst, welcher Anteil aller Hypothesen die Richtung der bewerteten Hypothese
teilt. Unabhängig von allen anderen Score-Modellen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from scores.base import BaseScoreModel, ScoreContext, ScoreModelOutput, consensus_fraction


class ConsensusScoreModel(BaseScoreModel):
    """Konsens-Score über die Richtungen aller Hypothesen (0..100)."""

    name = "consensus_score"
    value_range = "0..100"

    def compute(self, context: ScoreContext, params: Mapping[str, Any]) -> ScoreModelOutput:
        """Berechnet den Anteil richtungsgleicher Hypothesen als Score."""
        total = len(context.hypotheses)
        fraction = consensus_fraction(context.strategy_result, context.hypotheses)
        same = round(fraction * total)
        warnings: list[str] = []
        if total <= 1:
            warnings.append("Consensus: nur eine Hypothese – Aussagekraft begrenzt.")
        return ScoreModelOutput(
            name=self.name,
            value=float(fraction * 100.0),
            reasons=[
                f"{same}/{total} Hypothese(n) teilen die Richtung "
                f"'{context.strategy_result.direction.value}'."
            ],
            warnings=warnings,
        )
