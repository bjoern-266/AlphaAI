"""Drawdown Model – Kapitalkurven-Kennzahlen des Backtests.

Bewertet die Kapitalkurve: maximaler Drawdown (prozentual und absolut),
Endkapital und Gesamtrendite. Es nutzt ausschließlich die reinen Funktionen aus
:mod:`backtesting.equity_curve`; keine Handelsregel, kein anderes Modell.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backtesting import equity_curve as ec
from backtesting.base import BacktestContext, BacktestModelOutput, BaseBacktestModel


class DrawdownModel(BaseBacktestModel):
    """Berechnet Drawdown, Endkapital und Gesamtrendite aus der Kapitalkurve."""

    name = "drawdown_model"
    value_range = "Drawdown (0..100 %), Endkapital, Rendite"

    def compute(self, context: BacktestContext, params: Mapping[str, Any]) -> BacktestModelOutput:
        """Erzeugt die Drawdown-/Kapital-Kennzahlen aus der Kapitalkurve."""
        curve = context.equity_curve
        capital = context.starting_capital
        final = ec.final_equity(curve, capital)
        max_dd = ec.maximum_drawdown(curve)
        max_dd_abs = ec.maximum_drawdown_abs(curve)
        total_return = final - capital
        total_return_pct = (total_return / capital * 100.0) if capital > 0 else 0.0
        metrics = {
            "maximum_drawdown": max_dd,
            "maximum_drawdown_abs": max_dd_abs,
            "final_equity": final,
            "total_return": total_return,
            "total_return_pct": total_return_pct,
        }
        reasons = [
            f"Endkapital {final:.2f} ({total_return_pct:+.2f} %), " f"max. Drawdown {max_dd:.2f} %."
        ]
        return BacktestModelOutput(name=self.name, metrics=metrics, reasons=reasons)
