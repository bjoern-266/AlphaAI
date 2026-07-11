"""Journal Analysis – Kennzahlen aus dem Paper-Trading-Journal.

Wertet **ausschließlich** die bestehenden Journal-Einträge aus (nur Lesen, keine
Änderung am Journal). Ermittelt die Verteilung der Aktionen (OPEN/CLOSE/CANCEL/
EXPIRE), die Anzahl der Einträge, die realisierte Journal-Summe sowie Gewinner-/
Verlierer-Einträge. Reine Auswertung.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from analytics.base import AnalyticsContext, AnalyticsModelOutput, BaseAnalyticsModel
from models.paper_trading import OrderAction


class JournalAnalysisModel(BaseAnalyticsModel):
    """Berechnet Kennzahlen aus den bestehenden Journal-Einträgen."""

    name = "journal_analysis"
    value_range = "Journal-Kennzahlen (Aktionen, PnL, Gewinner/Verlierer)"

    def compute(self, context: AnalyticsContext, params: Mapping[str, Any]) -> AnalyticsModelOutput:
        """Wertet die Journal-Einträge aus (nur Lesen)."""
        journal = context.journal
        action_counts = {action.value: 0 for action in OrderAction}
        winners = 0
        losers = 0
        realized = 0.0
        for entry in journal:
            action_counts[entry.action.value] = action_counts.get(entry.action.value, 0) + 1
            if entry.action in (OrderAction.CLOSE, OrderAction.EXPIRE):
                realized += entry.pnl
                if entry.pnl > 0:
                    winners += 1
                elif entry.pnl < 0:
                    losers += 1

        statistics = {
            "total_entries": len(journal),
            "action_counts": action_counts,
            "closed_entries": action_counts.get("close", 0) + action_counts.get("expire", 0),
            "winners": winners,
            "losers": losers,
            "realized_pnl": realized,
        }
        warnings: list[str] = []
        if not journal:
            warnings.append("Kein Journal vorhanden (z. B. reiner Backtest) – Kennzahlen leer.")
        return AnalyticsModelOutput(
            name=self.name,
            statistics={"journal": statistics},
            metrics={"total_entries": float(len(journal))},
            reasons=[f"{len(journal)} Journal-Einträge ausgewertet."],
            warnings=warnings,
        )
