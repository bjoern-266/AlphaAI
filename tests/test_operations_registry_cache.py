"""Tests der Operations-Registry und des Operations-Caches."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from core.exceptions import AlphaAIError, CacheCapacityError, DuplicateRegistrationError
from engines.operations_cache import OperationsCache
from engines.operations_registry import OperationsRegistry, build_default_registry
from models.operations import JobDefinition, MarketClock, OperationReport

_EXPECTED = {
    "discovery",
    "scanner",
    "analytics",
    "market_intelligence",
    "dashboard_refresh",
    "paper_trading_update",
    "backtest_refresh",
}


# --- Registry -------------------------------------------------------------- #


def test_default_registry_has_all_jobs():
    assert set(build_default_registry().names()) == _EXPECTED


def test_default_registry_count():
    assert len(build_default_registry()) == 7


def test_discovery_is_exclusive():
    assert build_default_registry().get("discovery").exclusive is True


def test_analytics_not_exclusive():
    assert build_default_registry().get("analytics").exclusive is False


def test_registry_contains():
    registry = build_default_registry()
    assert "discovery" in registry
    assert "unknown" not in registry


def test_registry_get_unknown_raises():
    with pytest.raises(AlphaAIError):
        build_default_registry().get("missing")


def test_registry_duplicate_raises():
    registry = OperationsRegistry()
    registry.register(JobDefinition("discovery"))
    with pytest.raises(DuplicateRegistrationError):
        registry.register(JobDefinition("discovery"))


def test_custom_job_registration_without_engine_change():
    registry = OperationsRegistry()
    registry.register(JobDefinition("news_scan", "News Scan"))
    assert "news_scan" in registry


def test_registry_names_sorted():
    names = build_default_registry().names()
    assert names == sorted(names)


# --- Cache ----------------------------------------------------------------- #


def _report(tag: str) -> OperationReport:
    now = datetime(2024, 6, 3, tzinfo=UTC)
    return OperationReport(as_of=now, market_clock=MarketClock(as_of=now), metadata={"tag": tag})


def test_cache_set_get():
    cache = OperationsCache()
    report = _report("a")
    cache.set("k", report)
    assert cache.get("k") is report


def test_cache_miss():
    assert OperationsCache().get("x") is None


def test_cache_counters():
    cache = OperationsCache()
    cache.set("k", _report("a"))
    cache.get("k")
    cache.get("y")
    assert cache.hits == 1
    assert cache.misses == 1


def test_cache_fifo():
    cache = OperationsCache(capacity=2)
    cache.set("a", _report("a"))
    cache.set("b", _report("b"))
    cache.set("c", _report("c"))
    assert cache.get("a") is None


def test_cache_invalid_capacity():
    with pytest.raises(CacheCapacityError):
        OperationsCache(capacity=0)


def test_cache_is_operation_report():
    cache = OperationsCache()
    cache.set("k", _report("a"))
    assert isinstance(cache.get("k"), OperationReport)
