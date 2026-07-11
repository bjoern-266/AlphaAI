"""Pattern Analysis – Kennzahlen je Pattern-Label.

Gruppiert die Trades nach dem Pattern-Label aus der Metadata des Quell-Trades
und berechnet je Pattern Trades, Win Rate, Profit Factor sowie durchschnittlichen
Gewinn/Verlust. Führt das Quell-Trade **kein** Pattern-Label (die bestehenden
Reports geben es aktuell nicht je Trade her), fallen alle Trades in die Gruppe
``"unbekannt"`` – das Framework ist damit erweiterbar, sobald die Daten Labels
tragen, ohne dass eine Engine geändert werden muss. Reine Auswertung.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from analytics import aggregation as agg
from analytics.base import AnalyticsContext, AnalyticsModelOutput, BaseAnalyticsModel
from analytics.labeling import UNKNOWN, label_of


class PatternAnalysisModel(BaseAnalyticsModel):
    """Berechnet je Pattern-Label eine :class:`GroupStatistics`."""

    name = "pattern_analysis"
    value_range = "Kennzahlen je Pattern"

    def compute(self, context: AnalyticsContext, params: Mapping[str, Any]) -> AnalyticsModelOutput:
        """Gruppiert nach Pattern-Label und berechnet die Kennzahlen."""
        base_capital = float(context.config.get("base_capital", agg.DEFAULT_BASE_CAPITAL))
        key = str(context.config.get("pattern_label_key", "pattern"))
        stats = agg.grouped_statistics(
            context.trades, lambda t: label_of(t.labels, key), base_capital
        )
        warnings: list[str] = []
        if context.trades and set(stats) == {UNKNOWN}:
            warnings.append(
                "Kein Pattern-Label in den Daten – Gruppierung als 'unbekannt' "
                "(erweiterbar über Trade-Metadata)."
            )
        return AnalyticsModelOutput(
            name=self.name,
            statistics={"pattern": stats},
            metrics={"pattern_count": float(len(stats))},
            reasons=[f"{len(stats)} Pattern-Gruppe(n) ausgewertet."],
            warnings=warnings,
        )
