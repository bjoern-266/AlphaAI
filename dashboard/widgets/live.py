"""Widgets der Live-Analysis-Seite (nur Anzeige)."""

from __future__ import annotations

from dashboard import format as fmt
from dashboard.widgets.base import BaseWidget, WidgetContext
from models.dashboard import KIND_TABLE, TableSpec, WidgetSpec

_COLUMNS = (
    "Symbol",
    "Direction",
    "Strength",
    "Confidence",
    "Score",
    "Risk",
    "Pattern",
    "Strategy",
)


class WatchlistWidget(BaseWidget):
    """Watchlist mit Richtung, Stärke, Confidence, Score, Risiko, Pattern, Strategie."""

    name = "watchlist"
    title = "Live Watchlist"
    icon = "activity"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Watchlist-Tabelle aus dem Live-View-Model (nur Ablesen)."""
        vm = context.view_model.live
        rows = tuple(
            (
                row.symbol or "—",
                row.direction.upper(),
                row.strength.upper(),
                fmt.ratio_as_percent(row.confidence),
                fmt.number(row.score, 0),
                fmt.number(row.risk, 0),
                row.pattern,
                row.strategy,
            )
            for row in vm.rows
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_TABLE,
            table=TableSpec(columns=_COLUMNS, rows=rows),
            icon=self.icon,
            placeholder=not rows,
        )


class ReasonsWidget(BaseWidget):
    """Zeigt Reasons/Warnings der ersten Watchlist-Zeile."""

    name = "live_reasons"
    title = "Reasons & Warnings"
    icon = "target"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Reasons/Warnings-Liste (nur Ablesen)."""
        rows = context.view_model.live.rows
        if not rows:
            return WidgetSpec(
                widget_id=self.name, title=self.title, kind="list", icon=self.icon, placeholder=True
            )
        first = rows[0]
        items = tuple(f"• {reason}" for reason in first.reasons) + tuple(
            f"⚠ {warning}" for warning in first.warnings
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind="list",
            items=items,
            icon=self.icon,
            placeholder=not items,
        )
