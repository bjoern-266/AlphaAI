"""Widgets der Overview-Seite (nur Anzeige)."""

from __future__ import annotations

from dashboard import format as fmt
from dashboard.widgets.base import BaseWidget, WidgetContext
from dashboard.widgets.common import card
from models.dashboard import (
    KIND_CARDS,
    KIND_LIST,
    KIND_STATUS,
    TONE_ACCENT,
    TONE_DANGER,
    TONE_INFO,
    TONE_NEUTRAL,
    TONE_SUCCESS,
    TONE_WARNING,
    WidgetSpec,
)


class OverviewKpisWidget(BaseWidget):
    """Kennzahl-Kacheln der Übersicht."""

    name = "overview_kpis"
    title = "Command Overview"
    icon = "overview"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Kennzahl-Kacheln aus dem Overview-View-Model."""
        vm = context.view_model.overview
        cards = (
            card("Portfolio Value", fmt.currency(vm.portfolio_value), TONE_ACCENT, icon="layers"),
            card("Current Equity", fmt.currency(vm.current_equity), TONE_ACCENT),
            card("Today's PnL", fmt.signed_currency(vm.todays_pnl), _pnl_tone(vm.todays_pnl)),
            card(
                "Current Drawdown", fmt.percent(vm.current_drawdown), _dd_tone(vm.current_drawdown)
            ),
            card("Open Positions", fmt.integer(vm.open_positions), TONE_INFO),
            card("Closed Positions", fmt.integer(vm.closed_positions), TONE_INFO),
            card("Profit Factor", fmt.profit_factor(vm.profit_factor), TONE_SUCCESS),
            card("Win Rate", fmt.ratio_as_percent(vm.win_rate), TONE_SUCCESS),
            card("Recommendations", fmt.integer(vm.recommendation_count), TONE_INFO),
        )
        placeholder = vm.current_equity is None and vm.recommendation_count is None
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_CARDS,
            cards=cards,
            icon=self.icon,
            placeholder=placeholder,
        )


class SystemStatusWidget(BaseWidget):
    """System-Status aller Module."""

    name = "system_status"
    title = "System Status"
    icon = "signal"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Status-Anzeige aus dem Overview-View-Model."""
        statuses = context.view_model.overview.statuses
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_STATUS,
            status_items=statuses,
            icon=self.icon,
            placeholder=not statuses,
        )


class RecommendationFeedWidget(BaseWidget):
    """Kompakter Feed der aktuellen Empfehlungen."""

    name = "recommendation_feed"
    title = "Recommendation Feed"
    icon = "signal"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Empfehlungsliste aus dem Recommendation-View-Model."""
        rows = context.view_model.recommendations.rows
        items = tuple(
            f"{row.direction.upper()} / {row.strength.upper()} · "
            f"Score {fmt.number(row.score, 0)} · Conf {fmt.ratio_as_percent(row.confidence)}"
            for row in rows[:12]
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_LIST,
            items=items,
            icon=self.icon,
            placeholder=not items,
        )


def _pnl_tone(value: float | None) -> str:
    """Tönung eines PnL-Werts (grün/rot je Vorzeichen, neutral ohne Wert)."""
    if value is None:
        return TONE_NEUTRAL
    return TONE_SUCCESS if value >= 0 else TONE_DANGER


def _dd_tone(value: float | None) -> str:
    """Tönung eines Drawdown-Werts (Warnung, wenn vorhanden und > 0)."""
    if value is None:
        return TONE_NEUTRAL
    return TONE_WARNING if value > 0 else TONE_SUCCESS
