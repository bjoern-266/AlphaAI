"""Tests für den Strategy-Cache."""

from __future__ import annotations

import pytest

from engines.strategy_cache import StrategyCache
from engines.strategy_result import StrategyReport


def test_cache_hit_and_miss_counting() -> None:
    cache = StrategyCache(capacity=4)
    assert cache.get("a") is None
    cache.set("a", StrategyReport())
    assert cache.get("a") is not None
    assert cache.hits == 1
    assert cache.misses == 1


def test_cache_fifo_eviction() -> None:
    cache = StrategyCache(capacity=2)
    cache.set("a", StrategyReport())
    cache.set("b", StrategyReport())
    cache.set("c", StrategyReport())
    assert len(cache) == 2
    assert cache.get("a") is None


def test_cache_capacity_must_be_positive() -> None:
    with pytest.raises(ValueError):
        StrategyCache(capacity=0)


def test_cache_clear() -> None:
    cache = StrategyCache()
    cache.set("a", StrategyReport())
    cache.clear()
    assert len(cache) == 0
