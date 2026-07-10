"""Performance Model – Kapital-, Drawdown- und Exposure-Kennzahlen.

Fasst Startkapital, aktuellen Kontostand, Rendite, laufenden und maximalen
Drawdown, Exposure sowie realisierte/unrealisierte Ergebnisse zusammen. Nutzt
ausschließlich die reine Funktion aus :mod:`paper_trading.performance`.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from paper_trading import performance as perf
from paper_trading.base import (
    BasePaperTradingModel,
    PaperTradingContext,
    PaperTradingModelOutput,
)


class PerformanceModel(BasePaperTradingModel):
    """Berechnet die Kapital-/Drawdown-/Exposure-Kennzahlen aus dem Kontext."""

    name = "performance_model"
    value_range = "Kapital/Drawdown/Exposure"

    def compute(
        self, context: PaperTradingContext, params: Mapping[str, Any]
    ) -> PaperTradingModelOutput:
        """Erzeugt die Performance-Kennzahlen aus dem Kontext."""
        performance = perf.compute_performance(
            starting_capital=context.starting_capital,
            current_equity=context.current_equity,
            realized_pnl=context.realized_pnl,
            unrealized_pnl=context.unrealized_pnl,
            running_drawdown_pct=context.running_drawdown_pct,
            maximum_drawdown_pct=context.maximum_drawdown_pct,
            exposure_pct=context.exposure_pct,
            equity_curve=context.equity_curve,
        )
        metrics = {
            "current_equity": performance.current_equity,
            "portfolio_return_pct": performance.portfolio_return_pct,
            "running_drawdown_pct": performance.running_drawdown_pct,
            "maximum_drawdown_pct": performance.maximum_drawdown_pct,
            "portfolio_exposure_pct": performance.portfolio_exposure_pct,
            "realized_pnl": performance.realized_pnl,
            "unrealized_pnl": performance.unrealized_pnl,
        }
        reasons = [
            f"Kapital {performance.current_equity:.2f} "
            f"({performance.portfolio_return_pct:+.2f} %), "
            f"max. Drawdown {performance.maximum_drawdown_pct:.2f} %, "
            f"Exposure {performance.portfolio_exposure_pct:.1f} %."
        ]
        return PaperTradingModelOutput(
            name=self.name, metrics=metrics, reasons=reasons, details={"performance": performance}
        )
