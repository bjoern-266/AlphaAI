"""Ergebnistypen des Market-Discovery-Frameworks (Re-Export).

Die Definitionen liegen in der Entities-Schicht :mod:`models.market_discovery`.
Dieses Modul re-exportiert sie unter dem etablierten Pfad
``engines.market_discovery_result`` – konsistent mit
``engines.market_intelligence_result``.
"""

from __future__ import annotations

from models.market_discovery import (
    CandidateAnalysis,
    DiscoveryOpportunity,
    DiscoveryReport,
    DiscoveryStatistics,
    MarketDefinition,
    MarketSymbol,
    MarketUniverse,
    RejectedCandidate,
)

__all__ = [
    "MarketDefinition",
    "MarketSymbol",
    "MarketUniverse",
    "CandidateAnalysis",
    "RejectedCandidate",
    "DiscoveryOpportunity",
    "DiscoveryStatistics",
    "DiscoveryReport",
]
