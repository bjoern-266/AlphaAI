"""Widgets der Market-Intelligence-Seite (nur Anzeige des OpportunityReport).

Diese Widgets **visualisieren ausschließlich** den bereits fertigen
OpportunityReport (über das View Model). Sie **berechnen nichts** – sie
formatieren die vorhandenen Werte, filtern/suchen rein für die Anzeige.
"""

from __future__ import annotations

from dashboard import charts
from dashboard import format as fmt
from dashboard.viewmodels import OpportunityRow
from dashboard.widgets.base import BaseWidget, WidgetContext
from dashboard.widgets.common import card
from models.dashboard import (
    KIND_CARDS,
    KIND_CHART,
    KIND_LIST,
    KIND_TABLE,
    TONE_ACCENT,
    TONE_INFO,
    TONE_SUCCESS,
    TableSpec,
    WidgetSpec,
)

_COLUMNS = ("#", "Ticker", "Company", "Direction", "Strength", "Confidence", "Score", "Risk")


def _row_cells(row: OpportunityRow) -> tuple[str, ...]:
    """Formatiert eine Opportunity-Zeile für die Tabelle (nur Anzeige)."""
    return (
        str(row.rank),
        row.ticker or "—",
        row.company or "—",
        row.direction.upper(),
        row.strength.upper(),
        fmt.ratio_as_percent(row.confidence),
        fmt.number(row.score, 0),
        fmt.number(row.risk, 0),
    )


class TopOpportunitiesWidget(BaseWidget):
    """Die besten Chancen (Top-Auswahl aus dem Ranking)."""

    name = "mi_top_opportunities"
    title = "Top Opportunities"
    icon = "radar"
    limit = 10

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Tabelle der besten Chancen (reine Auswahl)."""
        rows = context.view_model.market_intelligence.rows[: self.limit]
        table_rows = tuple(_row_cells(row) for row in rows)
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_TABLE,
            table=TableSpec(columns=_COLUMNS, rows=table_rows),
            icon=self.icon,
            placeholder=not table_rows,
        )


class OpportunityRankingWidget(BaseWidget):
    """Vollständiges Ranking mit Suche und Richtungsfilter (nur Anzeige)."""

    name = "mi_ranking"
    title = "Opportunity Ranking"
    icon = "trending"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die (gefilterte/gesuchte) Ranking-Tabelle aus dem View Model."""
        rows = list(context.view_model.market_intelligence.rows)
        rows = _apply_search(rows, context.state.search_query)
        rows = _apply_direction(rows, context.state.get_filter("opportunity_direction", "all"))
        table_rows = tuple(_row_cells(row) for row in rows)
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_TABLE,
            table=TableSpec(columns=_COLUMNS, rows=table_rows),
            icon=self.icon,
            placeholder=not table_rows,
            metadata={
                "total": len(context.view_model.market_intelligence.rows),
                "shown": len(table_rows),
            },
        )


class OpportunityHeatmapWidget(BaseWidget):
    """Heatmap der Opportunity-Scores (Balken je Ticker)."""

    name = "mi_heatmap"
    title = "Opportunity Heatmap"
    icon = "activity"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Score-Heatmap aus den vorhandenen Scores (nur Anzeige)."""
        vm = context.view_model.market_intelligence
        chart = charts.bar_chart(
            "opportunity_heatmap",
            vm.heatmap_labels,
            vm.heatmap_scores,
            context.theme,
            name="Score",
            y_label="Opportunity Score",
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_CHART,
            chart=chart,
            icon=self.icon,
            placeholder=not vm.heatmap_scores,
        )


class OpportunityExplanationWidget(BaseWidget):
    """Transparente Herleitung der besten Chancen (keine Blackbox)."""

    name = "mi_explanation"
    title = "Warum diese Chancen?"
    icon = "target"
    limit = 5

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Erklärungsliste aus den vorhandenen Herleitungen."""
        explanations = context.view_model.market_intelligence.explanations[: self.limit]
        items: list[str] = []
        for exp in explanations:
            items.append(exp.headline)
            items.extend(f"   • {factor}" for factor in exp.factors)
            if exp.why_not_higher:
                items.append(f"   → {exp.why_not_higher}")
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_LIST,
            items=tuple(items),
            icon=self.icon,
            placeholder=not items,
        )


class MarketIntelligenceStatsWidget(BaseWidget):
    """Kennzahlen über alle bewerteten Chancen."""

    name = "mi_statistics"
    title = "Market Intelligence"
    icon = "signal"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Kennzahl-Kacheln aus der Opportunity-Statistik."""
        vm = context.view_model.market_intelligence
        cards = (
            card("Analysiert", fmt.integer(vm.analyzed_count), TONE_ACCENT),
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
            placeholder=vm.analyzed_count is None,
        )


def _apply_search(rows: list[OpportunityRow], query: str) -> list[OpportunityRow]:
    """Filtert Zeilen anhand eines Suchbegriffs (Ticker/Company/Branche/Markt)."""
    if not query:
        return rows
    needle = query.lower()
    return [
        row
        for row in rows
        if needle in row.ticker.lower()
        or needle in row.company.lower()
        or needle in row.sector.lower()
        or needle in row.market.lower()
    ]


def _apply_direction(rows: list[OpportunityRow], direction: str) -> list[OpportunityRow]:
    """Filtert Zeilen nach Richtung (``all`` = keine Einschränkung)."""
    if direction in ("", "all"):
        return rows
    return [row for row in rows if row.direction == direction]
