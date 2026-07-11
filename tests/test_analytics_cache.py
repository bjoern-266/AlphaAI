"""Tests für den Analytics-Cache (FIFO, Treffer/Fehltreffer)."""

from __future__ import annotations

import pytest

from core.exceptions import CacheCapacityError
from engines.analytics_cache import AnalyticsCache
from models.analytics import AnalyticsReport, AnalyticsResult, GroupStatistics


def _report(tag: str) -> AnalyticsReport:
    result = AnalyticsResult(
        analytics_id=tag,
        backtest_id="",
        paper_trading_id="",
        trade_count=0,
        win_rate=0.0,
        loss_rate=0.0,
        profit_factor=0.0,
        expectancy=0.0,
        average_winner=0.0,
        average_loser=0.0,
        maximum_drawdown=0.0,
        average_holding_time=0.0,
        average_risk_reward=0.0,
        long_statistics=GroupStatistics(label="long"),
        short_statistics=GroupStatistics(label="short"),
    )
    return AnalyticsReport(result=result, metadata={"tag": tag})


def test_set_and_get():
    cache = AnalyticsCache()
    report = _report("a")
    cache.set("k", report)
    assert cache.get("k") is report


def test_miss_returns_none():
    assert AnalyticsCache().get("x") is None


def test_hit_and_miss_counters():
    cache = AnalyticsCache()
    cache.set("k", _report("a"))
    cache.get("k")
    cache.get("x")
    assert cache.hits == 1
    assert cache.misses == 1


def test_fifo_eviction():
    cache = AnalyticsCache(capacity=2)
    cache.set("a", _report("a"))
    cache.set("b", _report("b"))
    cache.set("c", _report("c"))
    assert cache.get("a") is None
    assert cache.get("c") is not None


def test_len():
    cache = AnalyticsCache()
    cache.set("a", _report("a"))
    assert len(cache) == 1


def test_clear():
    cache = AnalyticsCache()
    cache.set("a", _report("a"))
    cache.clear()
    assert len(cache) == 0


def test_overwrite_same_key():
    cache = AnalyticsCache()
    second = _report("second")
    cache.set("k", _report("first"))
    cache.set("k", second)
    assert cache.get("k") is second


def test_invalid_capacity_raises():
    with pytest.raises(CacheCapacityError):
        AnalyticsCache(capacity=0)
