"""Widgets der Performance-Seite (nur Anzeige)."""

from __future__ import annotations

from dashboard import charts
from dashboard import format as fmt
from dashboard.widgets.base import BaseWidget, WidgetContext
from dashboard.widgets.common import card
from models.dashboard import KIND_CARDS, KIND_CHART, TONE_NEUTRAL, WidgetSpec


class PerformanceEquityWidget(BaseWidget):
    """Kapitalkurve (Performance)."""

    name = "performance_equity"
    title = "Equity Curve"
    icon = "trending"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Equity-Kurve aus dem Performance-View-Model (nur Ablesen)."""
        vm = context.view_model.performance
        chart = charts.area_chart(
            "performance_equity", vm.equity_curve, context.theme, x_labels=vm.equity_labels
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_CHART,
            chart=chart,
            icon=self.icon,
            placeholder=not vm.equity_curve,
        )


class DrawdownWidget(BaseWidget):
    """Drawdown-Kurve (Performance)."""

    name = "performance_drawdown"
    title = "Drawdown Curve"
    icon = "shield"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Drawdown-Kurve aus dem Performance-View-Model (nur Ablesen)."""
        vm = context.view_model.performance
        chart = charts.line_chart(
            "performance_drawdown",
            vm.drawdown_curve,
            context.theme,
            x_labels=vm.equity_labels,
            y_label="Drawdown %",
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_CHART,
            chart=chart,
            icon=self.icon,
            placeholder=not vm.drawdown_curve,
        )


class ProfitDistributionWidget(BaseWidget):
    """Verteilung der Trade-Ergebnisse (Performance)."""

    name = "performance_profit_distribution"
    title = "Profit Distribution"
    icon = "activity"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Ergebnis-Verteilung aus vorhandenen Trade-PnLs (nur Ablesen)."""
        values = context.view_model.performance.profit_distribution
        labels = tuple(str(i + 1) for i in range(len(values)))
        chart = charts.bar_chart(
            "profit_distribution", labels, values, context.theme, y_label="PnL"
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_CHART,
            chart=chart,
            icon=self.icon,
            placeholder=not values,
        )


class HoldingTimeWidget(BaseWidget):
    """Verteilung der Haltedauer (Performance)."""

    name = "performance_holding_time"
    title = "Holding Time Distribution"
    icon = "target"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Haltedauer-Verteilung aus der Zeit-Statistik (nur Ablesen)."""
        vm = context.view_model.performance
        chart = charts.bar_chart(
            "holding_time", vm.holding_labels, vm.holding_counts, context.theme, y_label="Trades"
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_CHART,
            chart=chart,
            icon=self.icon,
            placeholder=not vm.holding_counts,
        )


class ReturnsWidget(BaseWidget):
    """Monats-/Wochen-/Tagesrenditen (falls in den Reports vorhanden)."""

    name = "performance_returns"
    title = "Periodic Returns"
    icon = "signal"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Zeigt periodische Renditen – Platzhalter, wenn nicht in den Reports."""
        # Monats-/Wochen-/Tagesrenditen werden aktuell in keinem Report
        # gespeichert; sie werden als „nicht verfügbar" angezeigt (keine
        # Ersatzberechnung).
        cards = (
            card("Monthly Return", fmt.signed_percent(None), TONE_NEUTRAL),
            card("Weekly Return", fmt.signed_percent(None), TONE_NEUTRAL),
            card("Daily Return", fmt.signed_percent(None), TONE_NEUTRAL),
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_CARDS,
            cards=cards,
            icon=self.icon,
            placeholder=True,
        )
