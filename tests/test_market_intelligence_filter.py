"""Tests der Chancen-Filter (reine Auswahl, keine Berechnung)."""

from __future__ import annotations

from market_intelligence.filter import (
    OpportunityFilter,
    apply_filter,
    filter_by_direction,
    filter_by_max_risk,
    filter_by_min_confidence,
    filter_by_min_strength,
)
from models.recommendation import Direction, RecommendationStrength
from tests.market_intelligence_helpers import make_opportunity


def _sample():
    return [
        make_opportunity(
            "A",
            direction=Direction.LONG,
            confidence=0.9,
            risk=30.0,
            strength=RecommendationStrength.VERY_HIGH,
            market="NASDAQ",
            sector="Tech",
            exchange="NAS",
        ),
        make_opportunity(
            "B",
            direction=Direction.SHORT,
            confidence=0.5,
            risk=80.0,
            strength=RecommendationStrength.MEDIUM,
            market="NYSE",
            sector="Energy",
            exchange="NYSE",
        ),
        make_opportunity(
            "C",
            direction=Direction.NEUTRAL,
            confidence=0.3,
            risk=None,
            strength=RecommendationStrength.LOW,
            market="NASDAQ",
            sector="Tech",
            exchange="NAS",
        ),
    ]


def test_empty_filter_keeps_all():
    result = apply_filter(_sample(), OpportunityFilter())
    assert len(result) == 3


def test_filter_long():
    result = filter_by_direction(_sample(), "long")
    assert [o.ticker for o in result] == ["A"]


def test_filter_short():
    result = filter_by_direction(_sample(), "short")
    assert [o.ticker for o in result] == ["B"]


def test_filter_watch():
    result = filter_by_direction(_sample(), "watch")
    assert [o.ticker for o in result] == ["C"]


def test_filter_unknown_direction_excludes_all():
    result = filter_by_direction(_sample(), "sideways")
    assert result == ()


def test_filter_min_confidence():
    result = filter_by_min_confidence(_sample(), 0.6)
    assert [o.ticker for o in result] == ["A"]


def test_filter_max_risk_excludes_none():
    result = filter_by_max_risk(_sample(), 50.0)
    # A (30) bleibt; B (80) raus; C (None) raus.
    assert [o.ticker for o in result] == ["A"]


def test_filter_min_strength():
    result = filter_by_min_strength(_sample(), RecommendationStrength.MEDIUM)
    assert {o.ticker for o in result} == {"A", "B"}


def test_filter_by_market():
    result = apply_filter(_sample(), OpportunityFilter(market="NASDAQ"))
    assert {o.ticker for o in result} == {"A", "C"}


def test_filter_by_sector():
    result = apply_filter(_sample(), OpportunityFilter(sector="Energy"))
    assert [o.ticker for o in result] == ["B"]


def test_filter_by_exchange():
    result = apply_filter(_sample(), OpportunityFilter(exchange="NYSE"))
    assert [o.ticker for o in result] == ["B"]


def test_combined_filter():
    result = apply_filter(
        _sample(), OpportunityFilter(direction="long", min_confidence=0.5, market="NASDAQ")
    )
    assert [o.ticker for o in result] == ["A"]


def test_combined_filter_no_match():
    result = apply_filter(_sample(), OpportunityFilter(direction="short", market="NASDAQ"))
    assert result == ()


def test_filter_preserves_order():
    result = apply_filter(_sample(), OpportunityFilter(market="NASDAQ"))
    assert [o.ticker for o in result] == ["A", "C"]


def test_filter_is_frozen():
    import dataclasses

    import pytest

    opportunity_filter = OpportunityFilter()
    with pytest.raises(dataclasses.FrozenInstanceError):
        opportunity_filter.market = "X"  # type: ignore[misc]


def test_matches_single_opportunity():
    opp = make_opportunity("A", direction=Direction.LONG, confidence=0.8)
    assert OpportunityFilter(direction="long").matches(opp)
    assert not OpportunityFilter(direction="short").matches(opp)


def test_max_risk_boundary_inclusive():
    opp = make_opportunity("A", risk=50.0)
    assert OpportunityFilter(max_risk=50.0).matches(opp)


def test_min_confidence_boundary_inclusive():
    opp = make_opportunity("A", confidence=0.5)
    assert OpportunityFilter(min_confidence=0.5).matches(opp)
