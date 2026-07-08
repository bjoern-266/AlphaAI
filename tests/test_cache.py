"""Tests für den TTL-Cache."""

from __future__ import annotations

from core.config import CacheConfig
from data.cache import CacheCategory, TTLCache
from tests.helpers import FakeClock


def test_set_and_get(cache_config: CacheConfig) -> None:
    cache = TTLCache(cache_config, clock=FakeClock())
    cache.set("k", "value", CacheCategory.HISTORICAL)
    assert cache.get("k") == "value"


def test_get_missing_returns_none(cache_config: CacheConfig) -> None:
    cache = TTLCache(cache_config, clock=FakeClock())
    assert cache.get("unknown") is None


def test_entry_expires_after_ttl(cache_config: CacheConfig) -> None:
    clock = FakeClock()
    cache = TTLCache(cache_config, clock=clock)
    cache.set("k", "value", CacheCategory.INTRADAY)  # TTL = 10s
    clock.advance(9)
    assert cache.get("k") == "value"
    clock.advance(2)  # jetzt 11s > 10s
    assert cache.get("k") is None


def test_ttl_depends_on_category(cache_config: CacheConfig) -> None:
    cache = TTLCache(cache_config, clock=FakeClock())
    assert cache.ttl_for(CacheCategory.HISTORICAL) == 100
    assert cache.ttl_for(CacheCategory.INTRADAY) == 10
    assert cache.ttl_for(CacheCategory.TICKERLIST) == 1000


def test_disabled_cache_stores_nothing() -> None:
    disabled = CacheConfig(
        enabled=False,
        historical_ttl_seconds=100,
        intraday_ttl_seconds=10,
        tickerlist_ttl_seconds=1000,
    )
    cache = TTLCache(disabled, clock=FakeClock())
    cache.set("k", "value", CacheCategory.HISTORICAL)
    assert cache.get("k") is None
    assert len(cache) == 0


def test_invalidate_and_clear(cache_config: CacheConfig) -> None:
    cache = TTLCache(cache_config, clock=FakeClock())
    cache.set("a", 1, CacheCategory.HISTORICAL)
    cache.set("b", 2, CacheCategory.HISTORICAL)
    cache.invalidate("a")
    assert cache.get("a") is None
    assert cache.get("b") == 2
    cache.clear()
    assert cache.get("b") is None
