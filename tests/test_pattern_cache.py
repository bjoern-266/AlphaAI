"""Tests für den Pattern-Cache."""

from __future__ import annotations

import pytest

from engines.pattern_cache import PatternCache
from engines.pattern_result import PatternReport


def test_cache_hit_and_miss_counting() -> None:
    cache = PatternCache(capacity=4)
    assert cache.get("a") is None
    cache.set("a", PatternReport())
    assert cache.get("a") is not None
    assert cache.hits == 1
    assert cache.misses == 1


def test_cache_fifo_eviction() -> None:
    cache = PatternCache(capacity=2)
    cache.set("a", PatternReport())
    cache.set("b", PatternReport())
    cache.set("c", PatternReport())
    assert len(cache) == 2
    assert cache.get("a") is None


def test_cache_capacity_must_be_positive() -> None:
    with pytest.raises(ValueError):
        PatternCache(capacity=0)


def test_cache_clear() -> None:
    cache = PatternCache()
    cache.set("a", PatternReport())
    cache.clear()
    assert len(cache) == 0
