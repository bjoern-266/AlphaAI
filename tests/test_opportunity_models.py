"""Tests der Market-Intelligence-Modelle (unveränderlich, keine Berechnung)."""

from __future__ import annotations

import dataclasses

import pytest

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
from models.recommendation import Direction, RecommendationStrength
from tests.market_intelligence_helpers import make_opportunity


def test_market_candidate_defaults():
    candidate = MarketCandidate(ticker="AAPL")
    assert candidate.company == ""
    assert candidate.recommendation is None
    assert candidate.analytics is None
    assert candidate.metadata == {}


def test_market_candidate_is_frozen():
    candidate = MarketCandidate(ticker="AAPL")
    with pytest.raises(dataclasses.FrozenInstanceError):
        candidate.ticker = "TSLA"  # type: ignore[misc]


def test_model_output_defaults():
    out = OpportunityModelOutput(name="risk", score=70.0, weight=0.2)
    assert out.available is True
    assert out.reasons == []
    assert out.warnings == []


def test_opportunity_direction_properties():
    long_o = make_opportunity(direction=Direction.LONG)
    short_o = make_opportunity(direction=Direction.SHORT)
    watch_o = make_opportunity(direction=Direction.NEUTRAL)
    assert long_o.is_long and not long_o.is_short and not long_o.is_watch
    assert short_o.is_short and not short_o.is_long
    assert watch_o.is_watch and not watch_o.is_long


def test_opportunity_is_frozen():
    opportunity = make_opportunity()
    with pytest.raises(dataclasses.FrozenInstanceError):
        opportunity.opportunity_score = 10.0  # type: ignore[misc]


def test_opportunity_defaults():
    opportunity = Opportunity(
        ticker="AAPL",
        company="Apple",
        market="NASDAQ",
        direction=Direction.LONG,
        recommendation_strength=RecommendationStrength.HIGH,
        confidence=0.7,
        overall_rating=80.0,
        risk=60.0,
        opportunity_score=70.0,
    )
    assert opportunity.opportunity_rank == 0
    assert opportunity.reasons == ()
    assert opportunity.components == {}


def test_statistics_defaults():
    stats = OpportunityStatistics()
    assert stats.analyzed_count == 0
    assert stats.average_score is None
    assert stats.top_sectors == ()


def test_explanation_fields():
    exp = OpportunityExplanation(ticker="AAPL", rank=1, opportunity_score=80.0, headline="Platz 1")
    assert exp.factors == ()
    assert exp.risks == ()
    assert exp.why_not_higher == ""


def test_watchlist_size():
    watchlist = Watchlist(name="top", tickers=("AAPL", "TSLA"))
    assert watchlist.size == 2


def test_watchlist_empty_size():
    assert Watchlist(name="top").size == 0


def test_report_defaults():
    report = OpportunityReport()
    assert report.opportunities == ()
    assert report.opportunity_count == 0
    assert report.valid is True


def test_report_top():
    opps = tuple(make_opportunity(ticker=f"T{i}", rank=i + 1) for i in range(5))
    report = OpportunityReport(opportunities=opps)
    assert len(report.top(3)) == 3
    assert report.top(0) == ()
    assert len(report.top(99)) == 5


def test_report_by_rank():
    opps = (make_opportunity("A", rank=1), make_opportunity("B", rank=2))
    report = OpportunityReport(opportunities=opps)
    assert report.by_rank(2).ticker == "B"
    assert report.by_rank(9) is None


def test_report_by_ticker():
    opps = (make_opportunity("A", rank=1), make_opportunity("B", rank=2))
    report = OpportunityReport(opportunities=opps)
    assert report.by_ticker("A").opportunity_rank == 1
    assert report.by_ticker("Z") is None


def test_report_is_frozen():
    report = OpportunityReport()
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.valid = False  # type: ignore[misc]


def test_context_defaults():
    ctx = MarketIntelligenceContext(candidate=MarketCandidate(ticker="AAPL"))
    assert ctx.config == {}


def test_report_opportunity_count():
    opps = tuple(make_opportunity(ticker=f"T{i}") for i in range(4))
    assert OpportunityReport(opportunities=opps).opportunity_count == 4
