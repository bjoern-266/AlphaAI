"""Ratio Model – risikoadjustierte Kennzahlen (**vorbereitet**).

Berechnet Sharpe-, Sortino- und Calmar-Ratio mit ihren Standardformeln aus
:mod:`backtesting.statistics`. Die Kennzahlen sind bewusst **vorbereitet**: nicht
annualisiert/kalibriert (siehe ``docs/VALIDATION_REPORT.md``) und ``None`` bei zu
wenig Daten. Da ``None`` kein numerischer Metrik-Wert ist, werden die Ratios in
``details`` geführt. Keine Handelsregel, kein anderes Modell.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backtesting import equity_curve as ec
from backtesting import statistics as st
from backtesting.base import (
    BacktestContext,
    BacktestModelOutput,
    BaseBacktestModel,
    require_float,
    require_int,
)


class RatioModel(BaseBacktestModel):
    """Berechnet die vorbereiteten risikoadjustierten Kennzahlen."""

    name = "ratio_model"
    value_range = "Sharpe/Sortino/Calmar (vorbereitet, ggf. None)"

    def compute(self, context: BacktestContext, params: Mapping[str, Any]) -> BacktestModelOutput:
        """Erzeugt die (vorbereiteten) risikoadjustierten Kennzahlen."""
        risk_free_rate = require_float(params, "risk_free_rate", self.name)
        periods_per_year = require_int(params, "periods_per_year", self.name)

        returns = st.trade_returns(context.trades)
        capital = context.starting_capital
        final = ec.final_equity(context.equity_curve, capital)
        total_return_pct = ((final - capital) / capital * 100.0) if capital > 0 else 0.0
        max_dd = ec.maximum_drawdown(context.equity_curve)

        sharpe = st.sharpe_ratio(returns, risk_free_rate, periods_per_year)
        sortino = st.sortino_ratio(returns, risk_free_rate, periods_per_year)
        calmar = st.calmar_ratio(total_return_pct, max_dd)

        reasons = [
            "Risikoadjustierte Kennzahlen sind vorbereitet " "(nicht annualisiert/kalibriert)."
        ]
        return BacktestModelOutput(
            name=self.name,
            reasons=reasons,
            details={"sharpe": sharpe, "sortino": sortino, "calmar": calmar},
        )
