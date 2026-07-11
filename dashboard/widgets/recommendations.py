"""Widget der Recommendations-Seite (nur Anzeige)."""

from __future__ import annotations

from dashboard import format as fmt
from dashboard.widgets.base import BaseWidget, WidgetContext
from models.dashboard import KIND_TABLE, TableSpec, WidgetSpec

_COLUMNS = ("Symbol", "Direction", "Strength", "Confidence", "Score", "Risk", "Summary")


class RecommendationsTableWidget(BaseWidget):
    """Aktuelle Empfehlungen mit Richtung, Stärke, Confidence, Score, Risiko, Summary."""

    name = "recommendations_table"
    title = "Current Recommendations"
    icon = "signal"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Empfehlungstabelle aus dem View-Model (nur Ablesen)."""
        rows = tuple(
            (
                row.symbol or "—",
                row.direction.upper(),
                row.strength.upper(),
                fmt.ratio_as_percent(row.confidence),
                fmt.number(row.score, 0),
                fmt.number(row.risk, 0),
                row.summary,
            )
            for row in context.view_model.recommendations.rows
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_TABLE,
            table=TableSpec(columns=_COLUMNS, rows=rows),
            icon=self.icon,
            placeholder=not rows,
        )
