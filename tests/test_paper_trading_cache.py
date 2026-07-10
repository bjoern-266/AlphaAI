"""Tests für den Paper-Trading-Cache (FIFO, Treffer/Fehltreffer)."""

from __future__ import annotations

import pytest

from core.exceptions import CacheCapacityError
from engines.paper_trading_cache import PaperTradingCache
from models.paper_trading import PaperTradingReport


def _report(tag: str) -> PaperTradingReport:
    return PaperTradingReport(metadata={"tag": tag})


def test_set_and_get():
    cache = PaperTradingCache()
    report = _report("a")
    cache.set("k", report)
    assert cache.get("k") is report


def test_miss_returns_none():
    assert PaperTradingCache().get("x") is None


def test_hit_and_miss_counters():
    cache = PaperTradingCache()
    cache.set("k", _report("a"))
    cache.get("k")
    cache.get("x")
    assert cache.hits == 1
    assert cache.misses == 1


def test_fifo_eviction():
    cache = PaperTradingCache(capacity=2)
    cache.set("a", _report("a"))
    cache.set("b", _report("b"))
    cache.set("c", _report("c"))
    assert cache.get("a") is None
    assert cache.get("c") is not None


def test_len():
    cache = PaperTradingCache()
    cache.set("a", _report("a"))
    assert len(cache) == 1


def test_clear():
    cache = PaperTradingCache()
    cache.set("a", _report("a"))
    cache.clear()
    assert len(cache) == 0


def test_overwrite_same_key():
    cache = PaperTradingCache()
    second = _report("second")
    cache.set("k", _report("first"))
    cache.set("k", second)
    assert cache.get("k") is second


def test_invalid_capacity_raises():
    with pytest.raises(CacheCapacityError):
        PaperTradingCache(capacity=0)
