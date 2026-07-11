"""Market Analysis – Kennzahlen je Marktphase/Volatilität/Liquidität.

Gruppiert die Trades nach Marktphasen-, Volatilitäts- und Liquiditäts-Labels aus
der Metadata des Quell-Trades (z. B. Trend, Seitwärts, hohe/niedrige Volatilität).
Fehlen die Labels in den bestehenden Reports, fallen die Trades in die Gruppe
``"unbekannt"`` – erweiterbar, ohne eine Engine zu ändern. Reine Auswertung.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from analytics import aggregation as agg
from analytics.base import AnalyticsContext, AnalyticsModelOutput, BaseAnalyticsModel
from analytics.labeling import UNKNOWN, label_of


class MarketAnalysisModel(BaseAnalyticsModel):
    """Berechnet je Markt-Dimension eine :class:`GroupStatistics`."""

    name = "market_analysis"
    value_range = "Kennzahlen je Marktphase/Volatilität/Liquidität"

    def compute(self, context: AnalyticsContext, params: Mapping[str, Any]) -> AnalyticsModelOutput:
        """Gruppiert nach Marktphase, Volatilität und Liquidität."""
        base_capital = float(context.config.get("base_capital", agg.DEFAULT_BASE_CAPITAL))
        dimensions = {
            "market_phase": str(context.config.get("market_phase_label_key", "market_phase")),
            "volatility": str(context.config.get("volatility_label_key", "volatility")),
            "liquidity": str(context.config.get("liquidity_label_key", "liquidity")),
        }
        statistics: dict[str, Any] = {}
        for dimension, key in dimensions.items():
            statistics[dimension] = agg.grouped_statistics(
                context.trades, lambda t, k=key: label_of(t.labels, k), base_capital
            )

        warnings: list[str] = []
        if context.trades and all(set(g) == {UNKNOWN} for g in statistics.values()):
            warnings.append(
                "Keine Markt-Labels in den Daten – Gruppierung als 'unbekannt' "
                "(erweiterbar über Trade-Metadata)."
            )
        return AnalyticsModelOutput(
            name=self.name,
            statistics=statistics,
            metrics={"dimension_count": float(len(dimensions))},
            reasons=["Marktphase/Volatilität/Liquidität ausgewertet."],
            warnings=warnings,
        )
