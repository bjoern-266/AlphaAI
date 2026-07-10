"""Performance Model – die Kern-Kennzahlen des Backtests.

Fasst die grundlegenden Handelskennzahlen zusammen: Trefferquote, Verlustquote,
Profit Factor, durchschnittlicher Gewinn/Verlust, durchschnittliches
Chance-Risiko-Verhältnis, durchschnittliche Haltedauer und den Erwartungswert.
Es nutzt ausschließlich die reinen Funktionen aus
:mod:`backtesting.performance_metrics`; keine Handelsregel, kein anderes Modell.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backtesting import performance_metrics as pm
from backtesting.base import BacktestContext, BacktestModelOutput, BaseBacktestModel


class PerformanceModel(BaseBacktestModel):
    """Berechnet die grundlegenden Performance-Kennzahlen."""

    name = "performance_model"
    value_range = "Kennzahlen (Win Rate, Profit Factor, Expectancy, …)"

    def compute(self, context: BacktestContext, params: Mapping[str, Any]) -> BacktestModelOutput:
        """Erzeugt die Performance-Kennzahlen aus den simulierten Trades."""
        trades = context.trades
        metrics = {
            "win_rate": pm.win_rate(trades),
            "loss_rate": pm.loss_rate(trades),
            "profit_factor": pm.profit_factor(trades),
            "average_win": pm.average_win(trades),
            "average_loss": pm.average_loss(trades),
            "average_risk_reward": pm.average_risk_reward(trades),
            "average_holding_time": pm.average_holding_time(trades),
            "expectancy": pm.expectancy(trades),
            "expectancy_r": pm.expectancy_r(trades),
            "total_profit": pm.total_profit(trades),
        }
        reasons = [
            f"{len(trades)} Trades: Win Rate {metrics['win_rate'] * 100:.1f} %, "
            f"Profit Factor {metrics['profit_factor']:.2f}, "
            f"Expectancy {metrics['expectancy']:.2f} je Trade."
        ]
        warnings: list[str] = []
        if not trades:
            warnings.append("Keine Trades – Kennzahlen sind neutral (0).")
        return BacktestModelOutput(
            name=self.name, metrics=metrics, reasons=reasons, warnings=warnings
        )
