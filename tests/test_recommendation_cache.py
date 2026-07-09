"""Tests für den Recommendation-Cache."""

from __future__ import annotations

import pytest

from engines.recommendation_cache import RecommendationCache
from models.recommendation import RecommendationReport


def test_cache_hit_and_miss_counting() -> None:
    cache = RecommendationCache(capacity=4)
    assert cache.get("a") is None
    cache.set("a", RecommendationReport())
    assert cache.get("a") is not None
    assert cache.hits == 1
    assert cache.misses == 1


def test_cache_fifo_eviction() -> None:
    cache = RecommendationCache(capacity=2)
    cache.set("a", RecommendationReport())
    cache.set("b", RecommendationReport())
    cache.set("c", RecommendationReport())
    assert len(cache) == 2
    assert cache.get("a") is None


def test_cache_capacity_must_be_positive() -> None:
    with pytest.raises(ValueError):
        RecommendationCache(capacity=0)


def test_cache_clear() -> None:
    cache = RecommendationCache()
    cache.set("a", RecommendationReport())
    cache.clear()
    assert len(cache) == 0
