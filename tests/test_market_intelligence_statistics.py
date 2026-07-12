"""Tests der Opportunity-Statistik (reine Aggregation)."""

from __future__ import annotations

import pytest

from market_intelligence.statistics import compute_statistics
from models.recommendation import Direction
from tests.market_intelligence_helpers import make_opportunity


def _sample():
    return [
        make_opportunity(
            "A",
            score=90.0,
            confidence=0.9,
            risk=30.0,
            direction=Direction.LONG,
            sector="Tech",
            market="NASDAQ",
        ),
        make_opportunity(
            "B",
            score=70.0,
            confidence=0.7,
            risk=50.0,
            direction=Direction.SHORT,
            sector="Tech",
            market="NYSE",
        ),
        make_opportunity(
            "C",
            score=50.0,
            confidence=0.5,
            risk=None,
            direction=Direction.NEUTRAL,
            sector="Energy",
            market="NASDAQ",
        ),
    ]


def test_empty_statistics():
    stats = compute_statistics([])
    assert stats.analyzed_count == 0
    assert stats.average_score is None
    assert stats.top_sectors == ()


def test_analyzed_count():
    assert compute_statistics(_sample()).analyzed_count == 3


def test_direction_counts():
    stats = compute_statistics(_sample())
    assert stats.long_count == 1
    assert stats.short_count == 1
    assert stats.watch_count == 1


def test_average_score():
    stats = compute_statistics(_sample())
    assert stats.average_score == pytest.approx((90 + 70 + 50) / 3)


def test_average_risk_ignores_none():
    stats = compute_statistics(_sample())
    assert stats.average_risk == pytest.approx((30 + 50) / 2)


def test_average_confidence():
    stats = compute_statistics(_sample())
    assert stats.average_confidence == pytest.approx((0.9 + 0.7 + 0.5) / 3)


def test_top_sectors_counts():
    stats = compute_statistics(_sample())
    assert stats.top_sectors[0] == ("Tech", 2)
    assert ("Energy", 1) in stats.top_sectors


def test_top_markets_counts():
    stats = compute_statistics(_sample())
    assert stats.top_markets[0] == ("NASDAQ", 2)


def test_top_sectors_limit():
    opps = [make_opportunity(f"T{i}", sector=f"S{i}") for i in range(10)]
    stats = compute_statistics(opps, top_sectors=3)
    assert len(stats.top_sectors) == 3


def test_empty_sector_ignored():
    opps = [make_opportunity("A", sector=""), make_opportunity("B", sector="Tech")]
    stats = compute_statistics(opps)
    assert stats.top_sectors == (("Tech", 1),)


def test_all_risk_none_average_none():
    opps = [make_opportunity("A", risk=None), make_opportunity("B", risk=None)]
    stats = compute_statistics(opps)
    assert stats.average_risk is None


def test_single_opportunity():
    stats = compute_statistics([make_opportunity("A", score=42.0, direction=Direction.LONG)])
    assert stats.analyzed_count == 1
    assert stats.average_score == 42.0
    assert stats.long_count == 1
