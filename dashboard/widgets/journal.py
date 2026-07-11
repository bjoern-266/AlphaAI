"""Widget der Trade-Journal-Seite (nur Anzeige, mit Suche/Filter/Sortierung)."""

from __future__ import annotations

from dashboard import format as fmt
from dashboard.viewmodels import JournalRow
from dashboard.widgets.base import BaseWidget, WidgetContext
from models.dashboard import KIND_TABLE, TableSpec, WidgetSpec

_COLUMNS = ("Time", "Action", "Direction", "Strength", "Entry", "Exit", "PnL", "Reason")

# Zuordnung Sortierschlüssel → Sortierwert (reine Anzeige-Sortierung).
_SORT_KEYS = {
    "pnl": lambda row: row.pnl if row.pnl is not None else 0.0,
    "time": lambda row: row.timestamp,
    "direction": lambda row: row.direction,
    "strength": lambda row: row.strength,
}


class JournalTableWidget(BaseWidget):
    """Journal-Tabelle mit globaler Suche, Richtungsfilter und Sortierung.

    Suche/Filter/Sortierung sind reine **Anzeige**-Operationen über bereits
    vorhandene Zeilen – es wird nichts berechnet.
    """

    name = "journal_table"
    title = "Trade Journal"
    icon = "target"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die (gefilterte/sortierte) Journal-Tabelle aus dem View-Model."""
        rows = list(context.view_model.journal.rows)
        rows = _apply_search(rows, context.state.search_query)
        rows = _apply_direction(rows, context.state.get_filter("journal_direction", "all"))
        rows = _apply_sort(rows, context.state.get_sort("journal"))

        table_rows = tuple(
            (
                row.timestamp or "—",
                row.action.upper(),
                row.direction.upper(),
                row.strength.upper(),
                fmt.number(row.entry_price),
                fmt.number(row.exit_price),
                fmt.signed_currency(row.pnl),
                row.reason,
            )
            for row in rows
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_TABLE,
            table=TableSpec(columns=_COLUMNS, rows=table_rows),
            icon=self.icon,
            placeholder=not table_rows,
            metadata={"total": len(context.view_model.journal.rows), "shown": len(table_rows)},
        )


def _apply_search(rows: list[JournalRow], query: str) -> list[JournalRow]:
    """Filtert Zeilen anhand eines Suchbegriffs (Teilstring, Groß-/Kleinschreibung egal)."""
    if not query:
        return rows
    needle = query.lower()
    return [
        row
        for row in rows
        if needle in row.reason.lower()
        or needle in row.direction.lower()
        or needle in row.strength.lower()
        or needle in row.action.lower()
    ]


def _apply_direction(rows: list[JournalRow], direction: str) -> list[JournalRow]:
    """Filtert Zeilen nach Richtung (``all`` = keine Einschränkung)."""
    if direction in ("", "all"):
        return rows
    return [row for row in rows if row.direction == direction]


def _apply_sort(rows: list[JournalRow], sort: tuple[str, bool] | None) -> list[JournalRow]:
    """Sortiert Zeilen nach einem Anzeige-Schlüssel (falls gesetzt)."""
    if sort is None:
        return rows
    column, ascending = sort
    key = _SORT_KEYS.get(column)
    if key is None:
        return rows
    return sorted(rows, key=key, reverse=not ascending)
