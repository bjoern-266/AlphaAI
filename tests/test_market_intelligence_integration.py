"""End-to-End-Szenarien des Market-Intelligence-Frameworks.

Prüft die vollständige Kette von realistischen Kandidaten (mit ihren bereits
vorhandenen Reports) über die Engine bis zum priorisierten OpportunityReport,
inklusive Ranking, Statistik, Herleitung, Watchlists und Filter.
"""

from __future__ import annotations

import pytest

from engines.market_intelligence_engine import MarketIntelligenceEngine
from market_intelligence import filter as mi_filter
from market_intelligence import ranking
from models.recommendation import Direction, RecommendationStrength
from tests.market_intelligence_helpers import make_candidate, make_full_candidate


def _market():
    """Ein kleiner, gemischter Markt aus acht Aktien."""
    return [
        make_full_candidate(
            "AAA",
            rating=95.0,
            risk_factor=90.0,
            direction=Direction.LONG,
            sector="Tech",
            market="NASDAQ",
        ),
        make_full_candidate(
            "BBB",
            rating=88.0,
            risk_factor=70.0,
            direction=Direction.LONG,
            sector="Tech",
            market="NASDAQ",
        ),
        make_full_candidate(
            "CCC",
            rating=60.0,
            risk_factor=55.0,
            direction=Direction.SHORT,
            sector="Energy",
            market="NYSE",
        ),
        make_candidate(
            "DDD",
            rating=45.0,
            risk_factor=40.0,
            direction=Direction.SHORT,
            sector="Energy",
            market="NYSE",
        ),
        make_candidate(
            "EEE",
            rating=30.0,
            risk_factor=20.0,
            direction=Direction.LONG,
            sector="Finance",
            market="NYSE",
        ),
        make_full_candidate(
            "FFF",
            rating=75.0,
            risk_factor=65.0,
            direction=Direction.LONG,
            sector="Health",
            market="NASDAQ",
        ),
        make_candidate("GGG", with_recommendation=False, sector="Tech", market="NASDAQ"),
        make_full_candidate(
            "HHH",
            rating=82.0,
            risk_factor=80.0,
            direction=Direction.SHORT,
            sector="Tech",
            market="NASDAQ",
        ),
    ]


@pytest.fixture(scope="module")
def report():
    return MarketIntelligenceEngine.from_config().analyze(_market())


def test_report_valid(report):
    assert report.valid is True


def test_all_candidates_become_opportunities(report):
    assert report.opportunity_count == 8


def test_ranks_are_contiguous(report):
    ranks = [o.opportunity_rank for o in report.opportunities]
    assert ranks == list(range(1, 9))


def test_ranked_descending_by_score(report):
    scores = [o.opportunity_score for o in report.opportunities]
    assert scores == sorted(scores, reverse=True)


def test_best_is_aaa(report):
    assert report.opportunities[0].ticker == "AAA"


def test_watch_candidate_last(report):
    assert report.by_ticker("GGG").is_watch
    assert report.by_ticker("GGG").opportunity_score == 0.0


def test_statistics_counts(report):
    stats = report.statistics
    assert stats.analyzed_count == 8
    assert stats.long_count + stats.short_count + stats.watch_count == 8


def test_top_sectors_leads_with_tech(report):
    # Tech kommt viermal vor (AAA, BBB, GGG, HHH).
    assert report.statistics.top_sectors[0] == ("Tech", 4)


def test_top_markets(report):
    markets = dict(report.statistics.top_markets)
    assert markets["NASDAQ"] == 5


def test_watchlist_top_matches_ranking(report):
    top = report.watchlists["top"].tickers
    assert top[0] == report.opportunities[0].ticker


def test_long_watchlist_only_long(report):
    long_tickers = set(report.watchlists["long"].tickers)
    for ticker in long_tickers:
        assert report.by_ticker(ticker).is_long


def test_short_watchlist_only_short(report):
    for ticker in report.watchlists["short"].tickers:
        assert report.by_ticker(ticker).is_short


def test_every_opportunity_has_explanation(report):
    for opportunity in report.opportunities:
        assert opportunity.ticker in report.explanations


def test_rank_one_explanation_highest(report):
    top = report.opportunities[0]
    assert "Höchste" in report.explanations[top.ticker].why_not_higher


def test_lower_ranked_explains_gap(report):
    second = report.opportunities[1]
    assert report.opportunities[0].ticker in report.explanations[second.ticker].why_not_higher


def test_filter_long_on_report(report):
    longs = mi_filter.filter_by_direction(report.opportunities, "long")
    assert all(o.is_long for o in longs)


def test_filter_high_confidence(report):
    strong = mi_filter.filter_by_min_strength(report.opportunities, RecommendationStrength.HIGH)
    for opportunity in strong:
        assert ranking.strength_rank(opportunity.recommendation_strength) >= ranking.strength_rank(
            RecommendationStrength.HIGH
        )


def test_top5_selection(report):
    assert len(report.top(5)) == 5


def test_scores_all_within_bounds(report):
    for opportunity in report.opportunities:
        assert 0.0 <= opportunity.opportunity_score <= 100.0


def test_full_candidates_outrank_sparse(report):
    # AAA (alle Quellen, hohes Rating) steht vor EEE (nur Empfehlung, niedrig).
    assert report.by_ticker("AAA").opportunity_rank < report.by_ticker("EEE").opportunity_rank


def test_determinism(report):
    again = MarketIntelligenceEngine.from_config().analyze(_market())
    assert [o.ticker for o in again.opportunities] == [o.ticker for o in report.opportunities]


def test_components_recorded_for_full_candidate(report):
    components = report.by_ticker("AAA").components
    assert set(components) == {"recommendation", "risk", "analytics", "backtest", "paper_trading"}
