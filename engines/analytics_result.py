"""Ergebnistypen des Analytics-Frameworks (Re-Export).

Die Definitionen liegen in der Entities-Schicht :mod:`models.analytics`. Dieses
Modul re-exportiert sie unter dem etablierten Pfad ``engines.analytics_result`` –
konsistent mit ``engines.backtest_result`` und ``engines.paper_trading_result``.
"""

from __future__ import annotations

from models.analytics import (
    AnalyticsContext,
    AnalyticsModelOutput,
    AnalyticsReport,
    AnalyticsResult,
    AnalyticsTrade,
    GroupStatistics,
)

__all__ = [
    "AnalyticsResult",
    "AnalyticsReport",
    "AnalyticsContext",
    "AnalyticsModelOutput",
    "AnalyticsTrade",
    "GroupStatistics",
]
