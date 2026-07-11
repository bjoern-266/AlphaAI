"""Widgets der Backtesting-Seite (nur Anzeige)."""

from __future__ import annotations

from dashboard import charts
from dashboard import format as fmt
from dashboard.widgets.base import BaseWidget, WidgetContext
from dashboard.widgets.common import card
from models.dashboard import (
    KIND_CARDS,
    KIND_CHART,
    KIND_TABLE,
    TONE_ACCENT,
    TONE_SUCCESS,
    TONE_WARNING,
    TableSpec,
    WidgetSpec,
)

_TRADE_COLUMNS = (
    "Symbol",
    "Direction",
    "Strength",
    "Entry",
    "Exit",
    "PnL",
    "Outcome",
    "Exit Reason",
)


class BacktestKpisWidget(BaseWidget):
    """Kennzahl-Kacheln des Backtests."""

    name = "backtest_kpis"
    title = "Backtest Summary"
    icon = "database"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Backtest-Kacheln aus dem Backtest-View-Model."""
        vm = context.view_model.backtest
        cards = (
            card("Profit Factor", fmt.profit_factor(vm.profit_factor), TONE_SUCCESS),
            card("Win Rate", fmt.ratio_as_percent(vm.win_rate), TONE_SUCCESS),
            card("Max Drawdown", fmt.percent(vm.max_drawdown), TONE_WARNING),
            card("Total Return", fmt.signed_percent(vm.total_return_pct), TONE_ACCENT),
            card(
                f"Benchmark ({vm.benchmark_name or '—'})",
                fmt.signed_percent(vm.benchmark_return),
                TONE_ACCENT,
            ),
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_CARDS,
            cards=cards,
            icon=self.icon,
            placeholder=vm.profit_factor is None,
        )


class BacktestEquityWidget(BaseWidget):
    """Kapitalkurve des Backtests."""

    name = "backtest_equity"
    title = "Backtest Equity"
    icon = "trending"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut den Equity-Chart aus dem Backtest-View-Model (nur Ablesen)."""
        vm = context.view_model.backtest
        chart = charts.line_chart(
            "backtest_equity",
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


class TradeListWidget(BaseWidget):
    """Trade-Liste des Backtests."""

    name = "backtest_trades"
    title = "Trade List"
    icon = "target"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Trade-Tabelle aus dem Backtest-View-Model (nur Ablesen)."""
        rows = tuple(
            (
                t.symbol,
                t.direction.upper(),
                t.strength.upper(),
                fmt.number(t.entry_price),
                fmt.number(t.exit_price),
                fmt.signed_currency(t.pnl),
                t.outcome.upper(),
                t.exit_reason,
            )
            for t in context.view_model.backtest.trades
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_TABLE,
            table=TableSpec(columns=_TRADE_COLUMNS, rows=rows),
            icon=self.icon,
            placeholder=not rows,
        )
