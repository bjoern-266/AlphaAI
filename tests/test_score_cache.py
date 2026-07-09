"""Tests für den Score-Cache."""

from __future__ import annotations

import pytest

from engines.score_cache import ScoreCache
from engines.score_result import ScoreReport


def test_cache_hit_and_miss_counting() -> None:
    cache = ScoreCache(capacity=4)
    assert cache.get("a") is None
    cache.set("a", ScoreReport())
    assert cache.get("a") is not None
    assert cache.hits == 1
    assert cache.misses == 1


def test_cache_fifo_eviction() -> None:
    cache = ScoreCache(capacity=2)
    cache.set("a", ScoreReport())
    cache.set("b", ScoreReport())
    cache.set("c", ScoreReport())
    assert len(cache) == 2
    assert cache.get("a") is None


def test_cache_capacity_must_be_positive() -> None:
    with pytest.raises(ValueError):
        ScoreCache(capacity=0)


def test_cache_clear() -> None:
    cache = ScoreCache()
    cache.set("a", ScoreReport())
    cache.clear()
    assert len(cache) == 0
