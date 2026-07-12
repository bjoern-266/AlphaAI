"""Ergebnistypen des Market-Intelligence-Frameworks (Re-Export).

Die Definitionen liegen in der Entities-Schicht :mod:`models.opportunity`. Dieses
Modul re-exportiert sie unter dem etablierten Pfad
``engines.market_intelligence_result`` – konsistent mit
``engines.analytics_result`` und ``engines.backtest_result``.
"""

from __future__ import annotations

from models.opportunity import (
    MarketCandidate,
    MarketIntelligenceContext,
    Opportunity,
    OpportunityExplanation,
    OpportunityModelOutput,
    OpportunityReport,
    OpportunityStatistics,
    Watchlist,
)

__all__ = [
    "MarketCandidate",
    "MarketIntelligenceContext",
    "Opportunity",
    "OpportunityModelOutput",
    "OpportunityStatistics",
    "OpportunityExplanation",
    "Watchlist",
    "OpportunityReport",
]
