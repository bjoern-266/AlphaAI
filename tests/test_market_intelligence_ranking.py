"""Tests der Ranking-Bausteine und des Ranking-Zusammenbaus."""

from __future__ import annotations

from market_intelligence import ranking, ranking_engine
from models.recommendation import Direction, RecommendationStrength
from tests.market_intelligence_helpers import make_opportunity


def _sample():
    return [
        make_opportunity("A", score=50.0, confidence=0.9, risk=40.0),
        make_opportunity("C", score=80.0, confidence=0.5, risk=90.0),
        make_opportunity("B", score=65.0, confidence=0.7, risk=None),
    ]


def test_top_sizes_constant():
    assert ranking.TOP_SIZES == (5, 10, 20, 50)


def test_sort_criteria_constant():
    assert set(ranking.SORT_CRITERIA) == {
        "opportunity_score",
        "confidence",
        "risk",
        "recommendation",
        "alphabetical",
    }


def test_sort_by_score_desc():
    ordered = ranking.sort_opportunities(_sample(), ranking.SORT_SCORE)
    assert [o.ticker for o in ordered] == ["C", "B", "A"]


def test_sort_by_confidence():
    ordered = ranking.sort_opportunities(_sample(), ranking.SORT_CONFIDENCE)
    assert [o.ticker for o in ordered] == ["A", "B", "C"]


def test_sort_by_risk_none_last():
    ordered = ranking.sort_opportunities(_sample(), ranking.SORT_RISK)
    # C (90) > A (40) > B (None -> -1)
    assert [o.ticker for o in ordered] == ["C", "A", "B"]


def test_sort_alphabetical_ascending():
    ordered = ranking.sort_opportunities(_sample(), ranking.SORT_ALPHABETICAL)
    assert [o.ticker for o in ordered] == ["A", "B", "C"]


def test_sort_by_recommendation_strength():
    opps = [
        make_opportunity("A", strength=RecommendationStrength.LOW),
        make_opportunity("B", strength=RecommendationStrength.VERY_HIGH),
        make_opportunity("C", strength=RecommendationStrength.MEDIUM),
    ]
    ordered = ranking.sort_opportunities(opps, ranking.SORT_RECOMMENDATION)
    assert [o.ticker for o in ordered] == ["B", "C", "A"]


def test_strength_rank_order():
    assert ranking.strength_rank(RecommendationStrength.VERY_HIGH) > ranking.strength_rank(
        RecommendationStrength.HIGH
    )
    assert ranking.strength_rank(RecommendationStrength.REJECT) == 1


def test_assign_ranks():
    ordered = ranking.sort_opportunities(_sample(), ranking.SORT_SCORE)
    ranked = ranking.assign_ranks(ordered)
    assert [o.opportunity_rank for o in ranked] == [1, 2, 3]
    assert ranked[0].ticker == "C"


def test_assign_ranks_does_not_mutate_scores():
    ranked = ranking.assign_ranks(_sample())
    assert ranked[0].opportunity_score == 50.0


def test_top_selection():
    ordered = ranking.sort_opportunities(_sample(), ranking.SORT_SCORE)
    assert [o.ticker for o in ranking.top(ordered, 2)] == ["C", "B"]


def test_top_zero():
    assert ranking.top(_sample(), 0) == ()


def test_top_more_than_available():
    assert len(ranking.top(_sample(), 99)) == 3


def test_sort_empty():
    assert ranking.sort_opportunities([], ranking.SORT_SCORE) == ()


def test_sort_is_stable_for_equal_scores():
    opps = [make_opportunity("A", score=50.0), make_opportunity("B", score=50.0)]
    ordered = ranking.sort_opportunities(opps, ranking.SORT_SCORE)
    assert [o.ticker for o in ordered] == ["A", "B"]


# --- ranking_engine -------------------------------------------------------- #


def test_rank_sorts_and_assigns():
    ranked = ranking_engine.rank(_sample())
    assert [o.ticker for o in ranked] == ["C", "B", "A"]
    assert [o.opportunity_rank for o in ranked] == [1, 2, 3]


def test_rank_with_alphabetical():
    ranked = ranking_engine.rank(_sample(), ranking.SORT_ALPHABETICAL)
    assert [o.ticker for o in ranked] == ["A", "B", "C"]
    assert ranked[0].opportunity_rank == 1


def test_build_watchlists_top_long_short():
    opps = [
        make_opportunity("A", score=90.0, direction=Direction.LONG),
        make_opportunity("B", score=80.0, direction=Direction.SHORT),
        make_opportunity("C", score=70.0, direction=Direction.LONG),
    ]
    ranked = ranking_engine.rank(opps)
    watchlists = ranking_engine.build_watchlists(ranked, {})
    assert watchlists["top"].tickers == ("A", "B", "C")
    assert watchlists["long"].tickers == ("A", "C")
    assert watchlists["short"].tickers == ("B",)


def test_build_watchlists_respects_sizes():
    opps = [make_opportunity(f"T{i}", score=100.0 - i, direction=Direction.LONG) for i in range(5)]
    ranked = ranking_engine.rank(opps)
    watchlists = ranking_engine.build_watchlists(ranked, {"watchlist_top_size": 2})
    assert watchlists["top"].size == 2


def test_build_watchlists_titles():
    watchlists = ranking_engine.build_watchlists([], {})
    assert watchlists["long"].title == "Long Watchlist"
    assert watchlists["short"].title == "Short Watchlist"
