"""Tests für den Indikator-Cache."""

from __future__ import annotations

import pytest

from engines.indicator_cache import IndicatorCache
from engines.indicator_result import IndicatorResult


def test_cache_hit_and_miss_counting() -> None:
    cache = IndicatorCache(capacity=4)
    assert cache.get("a") is None  # Fehltreffer
    cache.set("a", IndicatorResult())
    assert cache.get("a") is not None  # Treffer
    assert cache.hits == 1
    assert cache.misses == 1


def test_cache_fifo_eviction() -> None:
    cache = IndicatorCache(capacity=2)
    cache.set("a", IndicatorResult())
    cache.set("b", IndicatorResult())
    cache.set("c", IndicatorResult())
    assert len(cache) == 2
    assert cache.get("a") is None  # ältester Eintrag verdrängt


def test_cache_capacity_must_be_positive() -> None:
    with pytest.raises(ValueError):
        IndicatorCache(capacity=0)


def test_cache_clear() -> None:
    cache = IndicatorCache()
    cache.set("a", IndicatorResult())
    cache.clear()
    assert len(cache) == 0
