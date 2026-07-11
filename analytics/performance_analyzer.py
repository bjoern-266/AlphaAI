"""Performance Analyzer – Kapitalkurve, Rendite und Drawdown.

Baut aus den Trades eine Kapitalkurve (``base_capital`` + kumulierter PnL) und
leitet daraus Rendite, maximalen Drawdown sowie bestes/schlechtestes Ergebnis ab.
Alle Werte werden so bereitgestellt, dass ein Dashboard sie direkt anzeigen kann.
Reine Auswertung, keine Bewertung.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from analytics import aggregation as agg
from analytics.base import AnalyticsContext, AnalyticsModelOutput, BaseAnalyticsModel


class PerformanceAnalyzer(BaseAnalyticsModel):
    """Berechnet Kapitalkurve, Rendite und Drawdown aus den Trades."""

    name = "performance_analyzer"
    value_range = "Kapital/Rendite/Drawdown"

    def compute(self, context: AnalyticsContext, params: Mapping[str, Any]) -> AnalyticsModelOutput:
        """Erzeugt die aggregierten Performance-Kennzahlen und die Kapitalkurve."""
        base_capital = float(context.config.get("base_capital", agg.DEFAULT_BASE_CAPITAL))
        trades = agg.chronological(context.trades)

        equity = base_capital
        curve = [base_capital]
        for trade in trades:
            equity += trade.pnl
            curve.append(equity)

        realized = agg.total_pnl(trades)
        total_return_pct = (realized / base_capital * 100.0) if base_capital > 0 else 0.0
        best = max((t.pnl for t in trades), default=0.0)
        worst = min((t.pnl for t in trades), default=0.0)

        metrics = {
            "base_capital": base_capital,
            "final_equity": equity,
            "total_pnl": realized,
            "total_return_pct": total_return_pct,
            "maximum_drawdown": agg.maximum_drawdown_pct(trades, base_capital),
            "best_trade": best,
            "worst_trade": worst,
        }
        return AnalyticsModelOutput(
            name=self.name,
            metrics=metrics,
            reasons=[
                f"Endkapital {equity:.2f} ({total_return_pct:+.2f} %), "
                f"max. Drawdown {metrics['maximum_drawdown']:.2f} %."
            ],
            details={"equity_curve": curve},
        )
