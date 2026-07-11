"""Recommendation Analysis – Kennzahlen je Recommendation Strength.

Gruppiert die Trades nach der Empfehlungsstärke (VERY_HIGH … REJECT) und
berechnet je Stärke Trades, Win Rate, Profit Factor und durchschnittliches
Ergebnis. Reine Auswertung, keine Bewertung.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from analytics import aggregation as agg
from analytics.base import AnalyticsContext, AnalyticsModelOutput, BaseAnalyticsModel


class RecommendationAnalysisModel(BaseAnalyticsModel):
    """Berechnet je Recommendation Strength eine :class:`GroupStatistics`."""

    name = "recommendation_analysis"
    value_range = "Kennzahlen je Recommendation Strength"

    def compute(self, context: AnalyticsContext, params: Mapping[str, Any]) -> AnalyticsModelOutput:
        """Gruppiert nach Empfehlungsstärke und berechnet die Kennzahlen."""
        base_capital = float(context.config.get("base_capital", agg.DEFAULT_BASE_CAPITAL))
        stats = agg.grouped_statistics(
            context.trades, lambda t: t.recommendation_strength.value, base_capital
        )
        return AnalyticsModelOutput(
            name=self.name,
            statistics={"recommendation_strength": stats},
            metrics={"strength_count": float(len(stats))},
            reasons=[f"{len(stats)} Empfehlungsstärke(n) ausgewertet."],
        )
