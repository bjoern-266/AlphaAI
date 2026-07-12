"""Fixtures für die Market-Discovery-Tests (Sprint 15)."""

from __future__ import annotations

from collections.abc import Sequence

from models.market_discovery import (
    CandidateAnalysis,
    DiscoveryOpportunity,
    MarketDefinition,
    MarketSymbol,
)
from models.recommendation import Direction, RecommendationStrength
from tests.dashboard_helpers import (
    make_analytics_report,
    make_backtest_report,
    make_paper_report,
    make_recommendation_result,
)


def make_symbol(
    ticker: str = "AAPL",
    company: str = "Apple",
    sector: str = "Tech",
    country: str = "US",
    exchange: str = "NASDAQ",
    market: str = "sp500",
    price: float | None = 180.0,
    volume: float | None = 5_000_000.0,
    average_dollar_volume: float | None = 900_000_000.0,
    history_days: int | None = 500,
    tradable: bool = True,
    delisted: bool = False,
) -> MarketSymbol:
    """Baut einen :class:`MarketSymbol` (Standard: sauberer, handelbarer Wert)."""
    return MarketSymbol(
        ticker=ticker,
        company=company,
        sector=sector,
        country=country,
        exchange=exchange,
        market=market,
        price=price,
        volume=volume,
        average_dollar_volume=average_dollar_volume,
        history_days=history_days,
        tradable=tradable,
        delisted=delisted,
    )


def make_analysis(
    ticker: str = "AAPL",
    direction: Direction = Direction.LONG,
    strength: RecommendationStrength = RecommendationStrength.HIGH,
    rating: float = 80.0,
    risk_factor: float = 60.0,
    confidence: float = 0.7,
    with_reports: bool = False,
) -> CandidateAnalysis:
    """Baut die vorhandenen Ergebnisse eines Werts (Empfehlung + optional Reports)."""
    recommendation = make_recommendation_result(
        rec_id=f"rec:{ticker}",
        direction=direction,
        strength=strength,
        confidence=confidence,
        rating=rating,
        risk_factor=risk_factor,
    )
    return CandidateAnalysis(
        recommendation=recommendation,
        analytics=make_analytics_report() if with_reports else None,
        backtest=make_backtest_report() if with_reports else None,
        paper_trading=make_paper_report() if with_reports else None,
    )


def make_symbol_source(
    universe: dict[str, Sequence[MarketSymbol]],
):
    """Erzeugt eine Symbol-Quelle aus einer ``markt -> Werte``-Zuordnung."""

    def source(definition: MarketDefinition) -> Sequence[MarketSymbol]:
        return universe.get(definition.name, [])

    return source


def make_analysis_provider(analyses: dict[str, CandidateAnalysis]):
    """Erzeugt eine Analyse-Quelle aus einer ``ticker -> CandidateAnalysis``-Zuordnung."""

    def provider(symbol: MarketSymbol) -> CandidateAnalysis:
        return analyses.get(symbol.ticker, CandidateAnalysis())

    return provider


def make_discovery_opportunity(
    ticker: str = "AAPL",
    rank: int = 1,
    score: float = 80.0,
    direction: Direction = Direction.LONG,
    sector: str = "Tech",
    market: str = "sp500",
    country: str = "US",
    confidence: float = 0.7,
    risk: float | None = 60.0,
    strength: RecommendationStrength = RecommendationStrength.HIGH,
) -> DiscoveryOpportunity:
    """Baut eine fertige :class:`DiscoveryOpportunity` (für VM/Statistik-Tests)."""
    return DiscoveryOpportunity(
        ticker=ticker,
        company=f"{ticker} Inc",
        sector=sector,
        country=country,
        exchange="NASDAQ",
        market=market,
        direction=direction,
        recommendation_strength=strength,
        confidence=confidence,
        risk=risk,
        opportunity_score=score,
        rank=rank,
        summary=f"{direction.value} {ticker}",
    )
