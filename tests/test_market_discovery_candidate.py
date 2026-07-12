"""Tests der Umwandlung Symbol ↔ Candidate ↔ DiscoveryOpportunity."""

from __future__ import annotations

from market_discovery.candidate import build_market_candidate, to_discovery_opportunity
from models.recommendation import Direction, RecommendationStrength
from tests.market_discovery_helpers import make_analysis, make_symbol
from tests.market_intelligence_helpers import make_opportunity


def test_build_market_candidate_copies_stammdaten():
    symbol = make_symbol("AAPL", company="Apple", sector="Tech", exchange="NASDAQ", market="sp500")
    candidate = build_market_candidate(symbol, make_analysis("AAPL"))
    assert candidate.ticker == "AAPL"
    assert candidate.company == "Apple"
    assert candidate.sector == "Tech"
    assert candidate.exchange == "NASDAQ"
    assert candidate.market == "sp500"


def test_build_market_candidate_country_in_metadata():
    symbol = make_symbol("SAP", country="DE")
    candidate = build_market_candidate(symbol, make_analysis("SAP"))
    assert candidate.metadata["country"] == "DE"


def test_build_market_candidate_attaches_reports():
    analysis = make_analysis("AAPL", with_reports=True)
    candidate = build_market_candidate(make_symbol("AAPL"), analysis)
    assert candidate.recommendation is not None
    assert candidate.analytics is not None
    assert candidate.backtest is not None
    assert candidate.paper_trading is not None


def test_build_market_candidate_without_analysis():
    from models.market_discovery import CandidateAnalysis

    candidate = build_market_candidate(make_symbol("X"), CandidateAnalysis())
    assert candidate.recommendation is None


def test_to_discovery_opportunity_adds_country_and_rank():
    opportunity = make_opportunity("AAPL", score=80.0, direction=Direction.LONG)
    symbol = make_symbol("AAPL", country="US", company="Apple Inc")
    discovery = to_discovery_opportunity(opportunity, symbol, rank=3)
    assert discovery.country == "US"
    assert discovery.rank == 3
    assert discovery.opportunity_score == 80.0


def test_to_discovery_opportunity_copies_fields():
    opportunity = make_opportunity(
        "AAPL",
        score=75.0,
        direction=Direction.SHORT,
        strength=RecommendationStrength.VERY_HIGH,
        confidence=0.8,
        risk=55.0,
    )
    discovery = to_discovery_opportunity(opportunity, make_symbol("AAPL"), rank=1)
    assert discovery.direction is Direction.SHORT
    assert discovery.recommendation_strength is RecommendationStrength.VERY_HIGH
    assert discovery.confidence == 0.8
    assert discovery.risk == 55.0


def test_to_discovery_opportunity_without_symbol():
    opportunity = make_opportunity("AAPL", company="Apple")
    discovery = to_discovery_opportunity(opportunity, None, rank=1)
    assert discovery.country == ""
    assert discovery.company == "Apple"


def test_to_discovery_opportunity_prefers_symbol_company():
    opportunity = make_opportunity("AAPL", company="Fallback")
    symbol = make_symbol("AAPL", company="Apple Inc")
    discovery = to_discovery_opportunity(opportunity, symbol, rank=1)
    assert discovery.company == "Apple Inc"


def test_to_discovery_opportunity_carries_summaries():
    from models.opportunity import Opportunity

    opportunity = Opportunity(
        ticker="AAPL",
        company="Apple",
        market="sp500",
        direction=Direction.LONG,
        recommendation_strength=RecommendationStrength.HIGH,
        confidence=0.7,
        overall_rating=80.0,
        risk=60.0,
        opportunity_score=70.0,
        analytics_summary="AN",
        backtest_summary="BT",
        paper_trading_summary="PT",
    )
    discovery = to_discovery_opportunity(opportunity, make_symbol("AAPL"), rank=1)
    assert discovery.analytics_summary == "AN"
    assert discovery.backtest_summary == "BT"
    assert discovery.paper_trading_summary == "PT"
