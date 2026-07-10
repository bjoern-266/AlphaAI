"""Tests für den Backtest-Cache (FIFO, Treffer/Fehltreffer)."""

from __future__ import annotations

import pytest

from core.exceptions import CacheCapacityError
from engines.backtest_cache import BacktestCache
from models.backtest import BacktestReport


def _report(tag: str) -> BacktestReport:
    return BacktestReport(metadata={"tag": tag})


def test_set_and_get():
    cache = BacktestCache()
    report = _report("a")
    cache.set("k", report)
    assert cache.get("k") is report


def test_miss_returns_none():
    cache = BacktestCache()
    assert cache.get("missing") is None


def test_hit_and_miss_counters():
    cache = BacktestCache()
    cache.set("k", _report("a"))
    cache.get("k")
    cache.get("x")
    assert cache.hits == 1
    assert cache.misses == 1


def test_fifo_eviction():
    cache = BacktestCache(capacity=2)
    cache.set("a", _report("a"))
    cache.set("b", _report("b"))
    cache.set("c", _report("c"))
    assert cache.get("a") is None
    assert cache.get("b") is not None
    assert cache.get("c") is not None


def test_len_reflects_entries():
    cache = BacktestCache()
    cache.set("a", _report("a"))
    cache.set("b", _report("b"))
    assert len(cache) == 2


def test_clear_empties_store():
    cache = BacktestCache()
    cache.set("a", _report("a"))
    cache.clear()
    assert len(cache) == 0


def test_overwrite_same_key():
    cache = BacktestCache()
    first = _report("first")
    second = _report("second")
    cache.set("k", first)
    cache.set("k", second)
    assert cache.get("k") is second


def test_invalid_capacity_raises():
    with pytest.raises(CacheCapacityError):
        BacktestCache(capacity=0)
