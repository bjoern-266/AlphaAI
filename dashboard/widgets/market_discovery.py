"""Widgets der Market-Discovery-Seite (nur Anzeige des DiscoveryReport).

Diese Widgets **visualisieren ausschließlich** den bereits fertigen
DiscoveryReport (über das View Model). Sie **berechnen nichts** – sie formatieren
die vorhandenen Werte und filtern/suchen rein für die Anzeige.
"""

from __future__ import annotations

from dashboard import format as fmt
from dashboard.viewmodels import DiscoveryRow
from dashboard.widgets.base import BaseWidget, WidgetContext
from dashboard.widgets.common import card
from models.dashboard import (
    KIND_CARDS,
    KIND_TABLE,
    TONE_ACCENT,
    TONE_INFO,
    TONE_SUCCESS,
    TONE_WARNING,
    TableSpec,
    WidgetSpec,
)

_COLUMNS = (
    "#",
    "Ticker",
    "Company",
    "Sector",
    "Country",
    "Direction",
    "Confidence",
    "Score",
    "Risk",
)
_SECTOR_COLUMNS = ("Branche", "Anzahl")
_MARKET_COLUMNS = ("Markt", "Anzahl")


def _row_cells(row: DiscoveryRow) -> tuple[str, ...]:
    """Formatiert eine Discovery-Zeile für die Tabelle (nur Anzeige)."""
    return (
        str(row.rank),
        row.ticker or "—",
        row.company or "—",
        row.sector or "—",
        row.country or "—",
        row.direction.upper(),
        fmt.ratio_as_percent(row.confidence),
        fmt.number(row.score, 0),
        fmt.number(row.risk, 0),
    )


class TopDiscoveryWidget(BaseWidget):
    """Die besten Chancen des Tages (Top-Auswahl aus der Discovery-Liste)."""

    name = "md_top_opportunities"
    title = "Top Opportunities"
    icon = "radar"
    limit = 10

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Tabelle der besten Chancen (reine Auswahl)."""
        rows = context.view_model.market_discovery.rows[: self.limit]
        table_rows = tuple(_row_cells(row) for row in rows)
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_TABLE,
            table=TableSpec(columns=_COLUMNS, rows=table_rows),
            icon=self.icon,
            placeholder=not table_rows,
        )


class DiscoveryRankingWidget(BaseWidget):
    """Vollständiges Ranking mit Suche und Filtern (Markt/Richtung)."""

    name = "md_ranking"
    title = "Discovery Ranking"
    icon = "trending"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die (gefilterte/gesuchte) Ranking-Tabelle aus dem View Model."""
        rows = list(context.view_model.market_discovery.rows)
        rows = _apply_search(rows, context.state.search_query)
        rows = _apply_direction(rows, context.state.get_filter("discovery_direction", "all"))
        rows = _apply_market(rows, context.state.get_filter("discovery_market", "all"))
        table_rows = tuple(_row_cells(row) for row in rows)
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_TABLE,
            table=TableSpec(columns=_COLUMNS, rows=table_rows),
            icon=self.icon,
            placeholder=not table_rows,
            metadata={
                "total": len(context.view_model.market_discovery.rows),
                "shown": len(table_rows),
            },
        )


class MarketOverviewWidget(BaseWidget):
    """Gesamtmarktübersicht (Universum, Vorfilter, Analysen)."""

    name = "md_market_overview"
    title = "Gesamtmarkt"
    icon = "database"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Kennzahl-Kacheln der Gesamtmarktübersicht."""
        vm = context.view_model.market_discovery
        cards = (
            card("Analysierte Aktien", fmt.integer(vm.universe_count), TONE_ACCENT),
            card("Verworfen", fmt.integer(vm.rejected_count), TONE_WARNING),
            card("Vollständige Analysen", fmt.integer(vm.analyzed_count), TONE_INFO),
            card("Long", fmt.integer(vm.long_count), TONE_SUCCESS),
            card("Short", fmt.integer(vm.short_count), TONE_INFO),
            card("Watch", fmt.integer(vm.watch_count), TONE_INFO),
            card("Ø Score", fmt.number(vm.average_score, 0), TONE_ACCENT),
            card("Ø Risiko", fmt.number(vm.average_risk, 0), TONE_INFO),
            card("Ø Confidence", fmt.ratio_as_percent(vm.average_confidence), TONE_INFO),
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_CARDS,
            cards=cards,
            icon=self.icon,
            placeholder=vm.universe_count is None,
        )


class SectorOverviewWidget(BaseWidget):
    """Branchenübersicht (häufigste Branchen)."""

    name = "md_sector_overview"
    title = "Branchen"
    icon = "layers"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Branchen-Tabelle aus den vorhandenen Zählungen."""
        rows = tuple(
            (name, str(count)) for name, count in context.view_model.market_discovery.top_sectors
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_TABLE,
            table=TableSpec(columns=_SECTOR_COLUMNS, rows=rows),
            icon=self.icon,
            placeholder=not rows,
        )


class MarketBreakdownWidget(BaseWidget):
    """Marktübersicht (häufigste Märkte)."""

    name = "md_market_breakdown"
    title = "Märkte"
    icon = "signal"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Markt-Tabelle aus den vorhandenen Zählungen."""
        rows = tuple(
            (name, str(count)) for name, count in context.view_model.market_discovery.top_markets
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_TABLE,
            table=TableSpec(columns=_MARKET_COLUMNS, rows=rows),
            icon=self.icon,
            placeholder=not rows,
        )


def _apply_search(rows: list[DiscoveryRow], query: str) -> list[DiscoveryRow]:
    """Filtert Zeilen anhand eines Suchbegriffs (Ticker/Company/Branche/Land/Markt)."""
    if not query:
        return rows
    needle = query.lower()
    return [
        row
        for row in rows
        if needle in row.ticker.lower()
        or needle in row.company.lower()
        or needle in row.sector.lower()
        or needle in row.country.lower()
        or needle in row.market.lower()
    ]


def _apply_direction(rows: list[DiscoveryRow], direction: str) -> list[DiscoveryRow]:
    """Filtert Zeilen nach Richtung (``all`` = keine Einschränkung)."""
    if direction in ("", "all"):
        return rows
    return [row for row in rows if row.direction == direction]


def _apply_market(rows: list[DiscoveryRow], market: str) -> list[DiscoveryRow]:
    """Filtert Zeilen nach Markt (``all`` = keine Einschränkung)."""
    if market in ("", "all"):
        return rows
    return [row for row in rows if row.market == market]
