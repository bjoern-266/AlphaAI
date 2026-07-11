"""Widgets der Paper-Portfolio-Seite (nur Anzeige)."""

from __future__ import annotations

from dashboard import charts
from dashboard import format as fmt
from dashboard.widgets.base import BaseWidget, WidgetContext
from dashboard.widgets.common import card
from models.dashboard import KIND_CARDS, KIND_CHART, TONE_ACCENT, TONE_INFO, WidgetSpec


class PortfolioKpisWidget(BaseWidget):
    """Kennzahl-Kacheln des Paper-Portfolios."""

    name = "portfolio_kpis"
    title = "Paper Portfolio"
    icon = "layers"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Portfolio-Kacheln aus dem Portfolio-View-Model."""
        vm = context.view_model.portfolio
        cards = (
            card("Portfolio Value", fmt.currency(vm.portfolio_value), TONE_ACCENT),
            card("Cash", fmt.currency(vm.cash), TONE_INFO),
            card("Exposure", fmt.percent(vm.exposure), TONE_INFO),
            card("Current Equity", fmt.currency(vm.current_equity), TONE_ACCENT),
            card("Realized PnL", fmt.signed_currency(vm.realized_pnl)),
            card("Unrealized PnL", fmt.signed_currency(vm.unrealized_pnl)),
            card("Today's PnL", fmt.signed_currency(vm.todays_pnl)),
            card("Open Positions", fmt.integer(vm.open_positions), TONE_INFO),
            card("Closed Positions", fmt.integer(vm.closed_positions), TONE_INFO),
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_CARDS,
            cards=cards,
            icon=self.icon,
            placeholder=vm.current_equity is None,
        )


class PortfolioEquityWidget(BaseWidget):
    """Kapitalkurve des Paper-Portfolios."""

    name = "portfolio_equity"
    title = "Equity Curve"
    icon = "trending"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut den Equity-Curve-Chart aus dem Portfolio-View-Model (nur Ablesen)."""
        vm = context.view_model.portfolio
        chart = charts.area_chart(
            "portfolio_equity",
            vm.equity_curve,
            context.theme,
            x_labels=vm.equity_labels,
            name="Equity",
            y_label="Equity",
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_CHART,
            chart=chart,
            icon=self.icon,
            placeholder=not vm.equity_curve,
        )
