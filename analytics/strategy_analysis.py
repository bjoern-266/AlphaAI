"""Strategy Analysis – Kennzahlen je Strategie.

Gruppiert die Trades nach der aus der ``recommendation_id`` abgeleiteten Strategie
und berechnet je Strategie Trades, Win Rate, Profit Factor, Drawdown und
durchschnittliche Haltedauer. Reine Auswertung, keine Bewertung.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from analytics import aggregation as agg
from analytics.base import AnalyticsContext, AnalyticsModelOutput, BaseAnalyticsModel


class StrategyAnalysisModel(BaseAnalyticsModel):
    """Berechnet je Strategie eine :class:`GroupStatistics`."""

    name = "strategy_analysis"
    value_range = "Kennzahlen je Strategie"

    def compute(self, context: AnalyticsContext, params: Mapping[str, Any]) -> AnalyticsModelOutput:
        """Gruppiert nach Strategie und berechnet die Kennzahlen."""
        base_capital = float(context.config.get("base_capital", agg.DEFAULT_BASE_CAPITAL))
        stats = agg.grouped_statistics(context.trades, lambda t: t.strategy, base_capital)
        return AnalyticsModelOutput(
            name=self.name,
            statistics={"strategy": stats},
            metrics={"strategy_count": float(len(stats))},
            reasons=[f"{len(stats)} Strategie(n) ausgewertet."],
        )
