"""Statistics Model – die Handelsstatistik des Paper-Portfolios.

Fasst Win/Loss Rate, Profit Factor, durchschnittlichen Gewinner/Verlierer,
durchschnittliche Haltedauer, Kapital, Rendite und die Positionszählung zusammen.
Nutzt ausschließlich die reinen Funktionen aus :mod:`paper_trading.statistics`.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from paper_trading import statistics as st
from paper_trading.base import (
    BasePaperTradingModel,
    PaperTradingContext,
    PaperTradingModelOutput,
)


class StatisticsModel(BasePaperTradingModel):
    """Berechnet die Handelsstatistik aus Trades und Positionen."""

    name = "statistics_model"
    value_range = "Kennzahlen (Win Rate, Profit Factor, …)"

    def compute(
        self, context: PaperTradingContext, params: Mapping[str, Any]
    ) -> PaperTradingModelOutput:
        """Erzeugt die Statistik-Kennzahlen aus dem Kontext."""
        stats = st.compute_statistics(
            trades=context.trades,
            open_positions=len(context.open_positions),
            closed_positions=len(context.closed_positions),
            current_equity=context.current_equity,
            starting_capital=context.starting_capital,
        )
        metrics = {
            "win_rate": stats.win_rate,
            "loss_rate": stats.loss_rate,
            "profit_factor": stats.profit_factor,
            "average_winner": stats.average_winner,
            "average_loser": stats.average_loser,
            "average_holding_time": stats.average_holding_time,
            "current_equity": stats.current_equity,
            "portfolio_return_pct": stats.portfolio_return_pct,
            "open_positions": float(stats.open_positions),
            "closed_positions": float(stats.closed_positions),
        }
        reasons = [
            f"{stats.closed_positions} geschlossen, {stats.open_positions} offen; "
            f"Win Rate {stats.win_rate * 100:.1f} %, Rendite {stats.portfolio_return_pct:+.2f} %."
        ]
        return PaperTradingModelOutput(
            name=self.name, metrics=metrics, reasons=reasons, details={"statistics": stats}
        )
