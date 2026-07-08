"""Gemeinsame Test-Fixtures für die Data Layer."""

from __future__ import annotations

import pytest

from core.config import CacheConfig


@pytest.fixture
def cache_config() -> CacheConfig:
    """Cache-Konfiguration mit kurzen TTLs für Tests."""
    return CacheConfig(
        enabled=True,
        historical_ttl_seconds=100,
        intraday_ttl_seconds=10,
        tickerlist_ttl_seconds=1000,
    )
