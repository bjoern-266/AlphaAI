"""Tests der Discovery-Statistik (reine Aggregation)."""

from __future__ import annotations

import pytest

from market_discovery.market_statistics import compute_statistics
from models.recommendation import Direction
from tests.market_discovery_helpers import make_discovery_opportunity


def _sample():
    return [
        make_discovery_opportunity(
            "A",
            score=90.0,
            confidence=0.9,
            risk=30.0,
            direction=Direction.LONG,
            sector="Tech",
            market="sp500",
        ),
        make_discovery_opportunity(
            "B",
            score=70.0,
            confidence=0.7,
            risk=50.0,
            direction=Direction.SHORT,
            sector="Tech",
            market="dax",
        ),
        make_discovery_opportunity(
            "C",
            score=50.0,
            confidence=0.5,
            risk=None,
            direction=Direction.NEUTRAL,
            sector="Energy",
            market="sp500",
        ),
    ]


def test_empty_opportunities():
    stats = compute_statistics(universe_count=100, rejected_count=40, opportunities=[])
    assert stats.universe_count == 100
    assert stats.rejected_count == 40
    assert stats.analyzed_count == 0
    assert stats.average_score is None


def test_counts():
    stats = compute_statistics(10, 4, _sample())
    assert stats.universe_count == 10
    assert stats.rejected_count == 4
    assert stats.analyzed_count == 3
    assert stats.long_count == 1
    assert stats.short_count == 1
    assert stats.watch_count == 1


def test_average_score():
    stats = compute_statistics(3, 0, _sample())
    assert stats.average_score == pytest.approx((90 + 70 + 50) / 3)


def test_average_risk_ignores_none():
    stats = compute_statistics(3, 0, _sample())
    assert stats.average_risk == pytest.approx((30 + 50) / 2)


def test_average_confidence():
    stats = compute_statistics(3, 0, _sample())
    assert stats.average_confidence == pytest.approx((0.9 + 0.7 + 0.5) / 3)


def test_top_sectors():
    stats = compute_statistics(3, 0, _sample())
    assert stats.top_sectors[0] == ("Tech", 2)


def test_top_markets():
    stats = compute_statistics(3, 0, _sample())
    assert stats.top_markets[0] == ("sp500", 2)


def test_top_sectors_limit():
    opps = [make_discovery_opportunity(f"T{i}", sector=f"S{i}") for i in range(8)]
    stats = compute_statistics(8, 0, opps, top_sectors=3)
    assert len(stats.top_sectors) == 3


def test_empty_sector_ignored():
    opps = [
        make_discovery_opportunity("A", sector=""),
        make_discovery_opportunity("B", sector="Tech"),
    ]
    stats = compute_statistics(2, 0, opps)
    assert stats.top_sectors == (("Tech", 1),)


def test_all_risk_none():
    opps = [make_discovery_opportunity("A", risk=None), make_discovery_opportunity("B", risk=None)]
    stats = compute_statistics(2, 0, opps)
    assert stats.average_risk is None
