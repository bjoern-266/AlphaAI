"""Risk Analysis – Kennzahlen je Risiko-Level.

Gruppiert die Trades nach dem aus den ``reasons`` abgeleiteten Risiko-Level
(low/medium/high) und berechnet je Level Win Rate, Profit Factor,
durchschnittlichen Verlust und maximalen Drawdown. Reine Auswertung.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from analytics import aggregation as agg
from analytics.base import AnalyticsContext, AnalyticsModelOutput, BaseAnalyticsModel
from analytics.labeling import UNKNOWN


class RiskAnalysisModel(BaseAnalyticsModel):
    """Berechnet je Risiko-Level eine :class:`GroupStatistics`."""

    name = "risk_analysis"
    value_range = "Kennzahlen je Risiko-Level"

    def compute(self, context: AnalyticsContext, params: Mapping[str, Any]) -> AnalyticsModelOutput:
        """Gruppiert nach Risiko-Level und berechnet die Kennzahlen."""
        base_capital = float(context.config.get("base_capital", agg.DEFAULT_BASE_CAPITAL))
        stats = agg.grouped_statistics(context.trades, lambda t: t.risk_level, base_capital)
        warnings: list[str] = []
        if context.trades and set(stats) == {UNKNOWN}:
            warnings.append("Kein Risiko-Level in den Daten ableitbar – Gruppe 'unbekannt'.")
        return AnalyticsModelOutput(
            name=self.name,
            statistics={"risk_level": stats},
            metrics={"risk_level_count": float(len(stats))},
            reasons=[f"{len(stats)} Risiko-Level ausgewertet."],
            warnings=warnings,
        )
