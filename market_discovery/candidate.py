"""Umwandlung zwischen Universum-Werten und Analyse-/Anzeige-Typen.

Baut aus einem :class:`~models.market_discovery.MarketSymbol` und dessen
**bereits vorhandenen** Ergebnissen einen :class:`~models.opportunity.MarketCandidate`
für den Market-Intelligence-Schritt und wandelt die bewertete
:class:`~models.opportunity.Opportunity` samt Stammdaten in eine
:class:`~models.market_discovery.DiscoveryOpportunity` um. Es findet **keine**
Berechnung statt – nur Zuordnung.
"""

from __future__ import annotations

from models.market_discovery import CandidateAnalysis, DiscoveryOpportunity, MarketSymbol
from models.opportunity import MarketCandidate, Opportunity


def build_market_candidate(symbol: MarketSymbol, analysis: CandidateAnalysis) -> MarketCandidate:
    """Baut einen :class:`MarketCandidate` aus Stammdaten und vorhandenen Reports."""
    return MarketCandidate(
        ticker=symbol.ticker,
        company=symbol.company,
        market=symbol.market,
        sector=symbol.sector,
        exchange=symbol.exchange,
        recommendation=analysis.recommendation,
        analytics=analysis.analytics,
        backtest=analysis.backtest,
        paper_trading=analysis.paper_trading,
        metadata={"country": symbol.country},
    )


def to_discovery_opportunity(
    opportunity: Opportunity, symbol: MarketSymbol | None, rank: int
) -> DiscoveryOpportunity:
    """Wandelt eine bewertete Chance samt Stammdaten in eine Discovery-Chance um."""
    country = symbol.country if symbol is not None else ""
    company = (
        symbol.company if symbol is not None and symbol.company else ""
    ) or opportunity.company
    return DiscoveryOpportunity(
        ticker=opportunity.ticker,
        company=company,
        sector=opportunity.sector,
        country=country,
        exchange=opportunity.exchange,
        market=opportunity.market,
        direction=opportunity.direction,
        recommendation_strength=opportunity.recommendation_strength,
        confidence=opportunity.confidence,
        risk=opportunity.risk,
        opportunity_score=opportunity.opportunity_score,
        rank=rank,
        summary=opportunity.summary,
        reasons=opportunity.reasons,
        warnings=opportunity.warnings,
        analytics_summary=opportunity.analytics_summary,
        backtest_summary=opportunity.backtest_summary,
        paper_trading_summary=opportunity.paper_trading_summary,
        timestamp=opportunity.timestamp,
    )
