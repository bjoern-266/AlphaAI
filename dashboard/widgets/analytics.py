"""Widgets der Analytics-Seite (nur Anzeige)."""

from __future__ import annotations

from dashboard import charts
from dashboard import format as fmt
from dashboard.widgets.base import BaseWidget, WidgetContext
from dashboard.widgets.common import card, group_statistics_table
from models.analytics import GroupStatistics
from models.dashboard import KIND_CARDS, KIND_CHART, KIND_TABLE, TONE_INFO, WidgetSpec


def _count(stat: GroupStatistics | None) -> int:
    """Trade-Anzahl einer optionalen Gruppenstatistik (0, falls fehlend)."""
    return stat.trade_count if stat is not None else 0


class LongShortWidget(BaseWidget):
    """LONG- vs. SHORT-Verteilung (Donut)."""

    name = "analytics_long_short"
    title = "Long vs Short"
    icon = "activity"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut den LONG/SHORT-Donut aus den bereits berechneten Zählungen."""
        vm = context.view_model.analytics
        chart = charts.donut_chart(
            "long_short",
            ("LONG", "SHORT"),
            (_count(vm.long_statistics), _count(vm.short_statistics)),
            context.theme,
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_CHART,
            chart=chart,
            icon=self.icon,
            placeholder=_count(vm.long_statistics) == 0 and _count(vm.short_statistics) == 0,
        )


class _GroupTableWidget(BaseWidget):
    """Basis für Analytics-Gruppentabellen (Strategie/Pattern/Risiko/…)."""

    stat_attr = ""

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut eine Gruppentabelle aus den bereits berechneten Statistiken."""
        groups = getattr(context.view_model.analytics, self.stat_attr, {})
        table = group_statistics_table(groups)
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_TABLE,
            table=table,
            icon=self.icon,
            placeholder=table.is_empty,
        )


class StrategyPerfWidget(_GroupTableWidget):
    """Kennzahlen je Strategie."""

    name = "analytics_strategy"
    title = "Strategy Performance"
    icon = "trending"
    stat_attr = "strategy_statistics"


class PatternPerfWidget(_GroupTableWidget):
    """Kennzahlen je Pattern."""

    name = "analytics_pattern"
    title = "Pattern Performance"
    icon = "layers"
    stat_attr = "pattern_statistics"


class RiskPerfWidget(_GroupTableWidget):
    """Kennzahlen je Risiko-Level."""

    name = "analytics_risk"
    title = "Risk Performance"
    icon = "shield"
    stat_attr = "risk_statistics"


class RecommendationPerfWidget(_GroupTableWidget):
    """Kennzahlen je Recommendation Strength."""

    name = "analytics_recommendation"
    title = "Recommendation Performance"
    icon = "signal"
    stat_attr = "recommendation_statistics"


class MarketPhaseWidget(_GroupTableWidget):
    """Kennzahlen je Marktphase/Volatilität/Liquidität."""

    name = "analytics_market"
    title = "Market Phase"
    icon = "radar"
    stat_attr = "market_statistics"


class TimeAnalysisWidget(BaseWidget):
    """Kennzahlen je Wochentag (Zeitanalyse)."""

    name = "analytics_time"
    title = "Time Analysis"
    icon = "activity"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Wochentag-Tabelle aus der Zeit-Statistik (nur Ablesen)."""
        weekday = context.view_model.analytics.time_statistics.get("weekday", {})
        table = group_statistics_table(weekday)
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_TABLE,
            table=table,
            icon=self.icon,
            placeholder=table.is_empty,
        )


class JournalAnalysisWidget(BaseWidget):
    """Kennzahlen aus der Journal-Analyse."""

    name = "analytics_journal"
    title = "Journal Analysis"
    icon = "database"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Journal-Kacheln aus der bereits berechneten Journal-Statistik."""
        journal = context.view_model.analytics.journal_statistics
        cards = (
            card("Total Entries", fmt.integer(journal.get("total_entries")), TONE_INFO),
            card("Closed", fmt.integer(journal.get("closed_entries")), TONE_INFO),
            card("Winners", fmt.integer(journal.get("winners"))),
            card("Losers", fmt.integer(journal.get("losers"))),
            card("Realized PnL", fmt.signed_currency(journal.get("realized_pnl"))),
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_CARDS,
            cards=cards,
            icon=self.icon,
            placeholder=not journal,
        )
