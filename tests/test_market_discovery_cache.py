"""Tests des Discovery-Caches (FIFO, Treffer/Fehltreffer)."""

from __future__ import annotations

import pytest

from core.exceptions import CacheCapacityError
from engines.market_discovery_cache import DiscoveryCache
from models.market_discovery import DiscoveryReport


def _report(tag: str) -> DiscoveryReport:
    return DiscoveryReport(metadata={"tag": tag})


def test_set_and_get():
    cache = DiscoveryCache()
    report = _report("a")
    cache.set("k", report)
    assert cache.get("k") is report


def test_miss_returns_none():
    assert DiscoveryCache().get("missing") is None


def test_hit_and_miss_counters():
    cache = DiscoveryCache()
    cache.set("k", _report("a"))
    cache.get("k")
    cache.get("nope")
    assert cache.hits == 1
    assert cache.misses == 1


def test_len():
    cache = DiscoveryCache()
    cache.set("a", _report("a"))
    cache.set("b", _report("b"))
    assert len(cache) == 2


def test_fifo_eviction():
    cache = DiscoveryCache(capacity=2)
    cache.set("a", _report("a"))
    cache.set("b", _report("b"))
    cache.set("c", _report("c"))
    assert cache.get("a") is None
    assert cache.get("c") is not None


def test_clear():
    cache = DiscoveryCache()
    cache.set("a", _report("a"))
    cache.clear()
    assert len(cache) == 0


def test_invalid_capacity():
    with pytest.raises(CacheCapacityError):
        DiscoveryCache(capacity=0)


def test_overwrite_same_key():
    cache = DiscoveryCache()
    cache.set("k", _report("a"))
    second = _report("b")
    cache.set("k", second)
    assert cache.get("k") is second


def test_is_discovery_report():
    cache = DiscoveryCache()
    cache.set("k", _report("a"))
    assert isinstance(cache.get("k"), DiscoveryReport)
