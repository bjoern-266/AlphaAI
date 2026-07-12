"""Tests des Opportunity-Caches (FIFO, Treffer/Fehltreffer)."""

from __future__ import annotations

import pytest

from core.exceptions import CacheCapacityError
from engines.market_intelligence_cache import OpportunityCache
from models.opportunity import OpportunityReport


def _report(tag: str) -> OpportunityReport:
    return OpportunityReport(metadata={"tag": tag})


def test_set_and_get():
    cache = OpportunityCache()
    report = _report("a")
    cache.set("k", report)
    assert cache.get("k") is report


def test_miss_returns_none():
    cache = OpportunityCache()
    assert cache.get("missing") is None


def test_hit_and_miss_counters():
    cache = OpportunityCache()
    cache.set("k", _report("a"))
    cache.get("k")
    cache.get("nope")
    assert cache.hits == 1
    assert cache.misses == 1


def test_len():
    cache = OpportunityCache()
    cache.set("a", _report("a"))
    cache.set("b", _report("b"))
    assert len(cache) == 2


def test_fifo_eviction():
    cache = OpportunityCache(capacity=2)
    cache.set("a", _report("a"))
    cache.set("b", _report("b"))
    cache.set("c", _report("c"))
    assert cache.get("a") is None  # ältester verdrängt
    assert cache.get("c") is not None


def test_clear():
    cache = OpportunityCache()
    cache.set("a", _report("a"))
    cache.clear()
    assert len(cache) == 0
    assert cache.get("a") is None


def test_invalid_capacity_raises():
    with pytest.raises(CacheCapacityError):
        OpportunityCache(capacity=0)


def test_overwrite_same_key():
    cache = OpportunityCache()
    cache.set("k", _report("a"))
    second = _report("b")
    cache.set("k", second)
    assert cache.get("k") is second


def test_is_cache_of_opportunity_report():
    cache = OpportunityCache()
    cache.set("k", _report("a"))
    assert isinstance(cache.get("k"), OpportunityReport)
