"""Gemeinsame Formatier-Bausteine für Widgets (reine Anzeige).

Diese Helfer wandeln bereits vorhandene Werte in Karten-/Tabellen-Beschreibungen
um. Sie **berechnen nichts** – sie formatieren nur (über :mod:`dashboard.format`)
und übernehmen die Werte unverändert.
"""

from __future__ import annotations

from collections.abc import Mapping

from dashboard import format as fmt
from models.analytics import GroupStatistics
from models.dashboard import MetricCard, TableSpec

_GROUP_COLUMNS = (
    "Gruppe",
    "Trades",
    "Win Rate",
    "Profit Factor",
    "Ø Gewinn",
    "Ø Verlust",
    "Max DD",
    "Total PnL",
)


def card(
    label: str, value: str, tone: str = "neutral", delta: str | None = None, icon: str = ""
) -> MetricCard:
    """Baut eine Kennzahl-Kachel aus einem bereits formatierten Wert."""
    return MetricCard(label=label, value=value, delta=delta, tone=tone, icon=icon)


def group_statistics_table(groups: Mapping[str, GroupStatistics]) -> TableSpec:
    """Baut eine Tabelle aus bereits berechneten :class:`GroupStatistics`.

    Es werden ausschließlich vorhandene Werte formatiert – keine Aggregation.
    """
    rows = tuple(
        (
            stat.label,
            fmt.integer(stat.trade_count),
            fmt.ratio_as_percent(stat.win_rate),
            fmt.profit_factor(stat.profit_factor),
            fmt.number(stat.average_winner),
            fmt.number(stat.average_loser),
            fmt.percent(stat.maximum_drawdown),
            fmt.number(stat.total_pnl),
        )
        for stat in groups.values()
    )
    return TableSpec(columns=_GROUP_COLUMNS, rows=rows)
