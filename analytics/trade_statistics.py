"""Trade Statistics – die aggregierten Kern-Kennzahlen und LONG/SHORT.

Berechnet die Gesamt-Kennzahlen über alle Trades sowie getrennte Statistiken für
LONG und SHORT. Nutzt ausschließlich die reinen Bausteine aus
:mod:`analytics.aggregation`. Keine Bewertung, keine Handelsregel.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from analytics import aggregation as agg
from analytics.base import AnalyticsContext, AnalyticsModelOutput, BaseAnalyticsModel


class TradeStatisticsModel(BaseAnalyticsModel):
    """Aggregierte Kern-Kennzahlen und LONG-/SHORT-Statistik."""

    name = "trade_statistics"
    value_range = "Kennzahlen (Win Rate, Profit Factor, Expectancy, LONG/SHORT)"

    def compute(self, context: AnalyticsContext, params: Mapping[str, Any]) -> AnalyticsModelOutput:
        """Erzeugt Gesamt-, LONG- und SHORT-Kennzahlen."""
        base_capital = float(context.config.get("base_capital", agg.DEFAULT_BASE_CAPITAL))
        trades = context.trades
        overall = agg.group_statistics("overall", trades, base_capital)
        long_stats = agg.group_statistics("long", context.long_trades, base_capital)
        short_stats = agg.group_statistics("short", context.short_trades, base_capital)

        metrics = {
            "trade_count": float(overall.trade_count),
            "win_rate": overall.win_rate,
            "loss_rate": overall.loss_rate,
            "profit_factor": overall.profit_factor,
            "expectancy": agg.expectancy(trades),
            "average_winner": overall.average_winner,
            "average_loser": overall.average_loser,
            "maximum_drawdown": overall.maximum_drawdown,
            "average_holding_time": overall.average_holding_time,
            "average_risk_reward": agg.average_risk_reward(trades),
        }
        warnings: list[str] = []
        if not trades:
            warnings.append("Keine Trades – Kennzahlen sind neutral (0).")
        return AnalyticsModelOutput(
            name=self.name,
            metrics=metrics,
            statistics={"overall": overall, "long": long_stats, "short": short_stats},
            reasons=[
                f"{overall.trade_count} Trades "
                f"({long_stats.trade_count} LONG / {short_stats.trade_count} SHORT), "
                f"Win Rate {overall.win_rate * 100:.1f} %, "
                f"Profit Factor {overall.profit_factor:.2f}."
            ],
            warnings=warnings,
        )
