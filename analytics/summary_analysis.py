"""Summary Analysis – menschenlesbare Zusammenfassung.

Fasst die wichtigsten Kennzahlen in einem kurzen, reproduzierbaren Text zusammen.
Nutzt ausschließlich die reinen Bausteine aus :mod:`analytics.aggregation`.
Reine Auswertung, keine Bewertung, keine Handlungsempfehlung.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from analytics import aggregation as agg
from analytics.base import AnalyticsContext, AnalyticsModelOutput, BaseAnalyticsModel


class SummaryAnalysisModel(BaseAnalyticsModel):
    """Erzeugt eine kompakte Text-Zusammenfassung der Analyse."""

    name = "summary_analysis"
    value_range = "Text-Zusammenfassung"

    def compute(self, context: AnalyticsContext, params: Mapping[str, Any]) -> AnalyticsModelOutput:
        """Baut die Zusammenfassung aus den Kern-Kennzahlen."""
        trades = context.trades
        base_capital = float(context.config.get("base_capital", agg.DEFAULT_BASE_CAPITAL))
        if not trades:
            summary = "Keine Trades ausgewertet – keine Statistik verfügbar."
        else:
            summary = (
                f"{len(trades)} Trades ausgewertet: "
                f"Win Rate {agg.win_rate(trades) * 100:.1f} %, "
                f"Profit Factor {agg.profit_factor(trades):.2f}, "
                f"Expectancy {agg.expectancy(trades):.2f}, "
                f"max. Drawdown {agg.maximum_drawdown_pct(trades, base_capital):.2f} %. "
                f"LONG {len(context.long_trades)} / SHORT {len(context.short_trades)}."
            )
        return AnalyticsModelOutput(
            name=self.name,
            reasons=[summary],
            details={"summary": summary},
        )
