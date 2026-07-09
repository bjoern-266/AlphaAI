"""Tests für den Risk-Cache."""

from __future__ import annotations

import pytest

from engines.risk_cache import RiskCache
from models.risk import RiskReport


def test_cache_hit_and_miss_counting() -> None:
    cache = RiskCache(capacity=4)
    assert cache.get("a") is None
    cache.set("a", RiskReport())
    assert cache.get("a") is not None
    assert cache.hits == 1
    assert cache.misses == 1


def test_cache_fifo_eviction() -> None:
    cache = RiskCache(capacity=2)
    cache.set("a", RiskReport())
    cache.set("b", RiskReport())
    cache.set("c", RiskReport())
    assert len(cache) == 2
    assert cache.get("a") is None


def test_cache_capacity_must_be_positive() -> None:
    with pytest.raises(ValueError):
        RiskCache(capacity=0)


def test_cache_clear() -> None:
    cache = RiskCache()
    cache.set("a", RiskReport())
    cache.clear()
    assert len(cache) == 0
