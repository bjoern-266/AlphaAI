"""Fixtures für die Market-Intelligence-Tests (Sprint 14)."""

from __future__ import annotations

from datetime import UTC, datetime

from models.opportunity import MarketCandidate, Opportunity
from models.recommendation import Direction, RecommendationStrength
from tests.dashboard_helpers import (
    make_analytics_report,
    make_backtest_report,
    make_paper_report,
    make_recommendation_result,
)

_T0 = datetime(2024, 1, 1, tzinfo=UTC)


def make_candidate(
    ticker: str = "AAPL",
    company: str = "Apple",
    market: str = "NASDAQ",
    sector: str = "Tech",
    exchange: str = "NAS",
    direction: Direction = Direction.LONG,
    strength: RecommendationStrength = RecommendationStrength.HIGH,
    rating: float = 80.0,
    risk_factor: float = 60.0,
    confidence: float = 0.7,
    with_recommendation: bool = True,
    with_analytics: bool = False,
    with_backtest: bool = False,
    with_paper: bool = False,
    pattern_summary: str = "",
    strategy_summary: str = "",
) -> MarketCandidate:
    """Baut einen :class:`MarketCandidate` mit wählbaren Quellen."""
    recommendation = None
    if with_recommendation:
        recommendation = make_recommendation_result(
            rec_id=f"rec:{ticker}",
            direction=direction,
            strength=strength,
            confidence=confidence,
            rating=rating,
            risk_factor=risk_factor,
        )
    return MarketCandidate(
        ticker=ticker,
        company=company,
        market=market,
        sector=sector,
        exchange=exchange,
        recommendation=recommendation,
        analytics=make_analytics_report() if with_analytics else None,
        backtest=make_backtest_report() if with_backtest else None,
        paper_trading=make_paper_report() if with_paper else None,
        pattern_summary=pattern_summary,
        strategy_summary=strategy_summary,
    )


def make_full_candidate(ticker: str = "AAPL", **kwargs) -> MarketCandidate:
    """Baut einen Kandidaten mit allen Quellen (Recommendation/Analytics/BT/PT)."""
    kwargs.setdefault("with_analytics", True)
    kwargs.setdefault("with_backtest", True)
    kwargs.setdefault("with_paper", True)
    return make_candidate(ticker, **kwargs)


def make_opportunity(
    ticker: str = "AAPL",
    score: float = 75.0,
    rank: int = 0,
    direction: Direction = Direction.LONG,
    strength: RecommendationStrength = RecommendationStrength.HIGH,
    confidence: float = 0.7,
    risk: float | None = 60.0,
    market: str = "NASDAQ",
    sector: str = "Tech",
    exchange: str = "NAS",
    company: str = "Apple",
    reasons: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (),
    components: dict[str, float] | None = None,
) -> Opportunity:
    """Baut eine fertige :class:`Opportunity` (für Ranking/Filter/Statistik)."""
    return Opportunity(
        ticker=ticker,
        company=company,
        market=market,
        direction=direction,
        recommendation_strength=strength,
        confidence=confidence,
        overall_rating=score,
        risk=risk,
        opportunity_score=score,
        opportunity_rank=rank,
        summary=f"{direction.value} {ticker}",
        sector=sector,
        exchange=exchange,
        reasons=reasons,
        warnings=warnings,
        components=components or {"recommendation": score, "risk": risk or 0.0},
        timestamp=_T0,
    )
