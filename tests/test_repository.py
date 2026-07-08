"""Tests für das MarketRepository (Cache + Provider + Validierung)."""

from __future__ import annotations

import numpy as np

from core.config import CacheConfig
from data.cache import TTLCache
from data.market_request import MarketRequest
from data.market_result import MarketResult, MarketStatus
from data.validator import MarketDataValidator
from providers.base_provider import BaseProvider
from repositories.market_repository import MarketRepository
from tests.helpers import FakeClock, make_ohlcv


class CountingProvider(BaseProvider):
    """Provider-Attrappe, die Aufrufe zählt und ein festes Ergebnis liefert."""

    name = "fake"

    def __init__(self, result: MarketResult) -> None:
        self._result = result
        self.calls = 0

    def fetch(self, request: MarketRequest) -> MarketResult:
        self.calls += 1
        return self._result


def _make_repo(provider: BaseProvider, cache_config: CacheConfig) -> MarketRepository:
    cache = TTLCache(cache_config, clock=FakeClock())
    return MarketRepository(provider, cache, MarketDataValidator())


def test_second_call_hits_cache(cache_config: CacheConfig) -> None:
    result = MarketResult(provider="fake", status=MarketStatus.OK, data={"AAPL": make_ohlcv()})
    provider = CountingProvider(result)
    repo = _make_repo(provider, cache_config)
    request = MarketRequest(("AAPL",), "6mo", "1d")

    repo.get_market_data(request)
    repo.get_market_data(request)
    assert provider.calls == 1  # zweiter Aufruf aus dem Cache


def test_use_cache_false_bypasses_cache(cache_config: CacheConfig) -> None:
    result = MarketResult(provider="fake", status=MarketStatus.OK, data={"AAPL": make_ohlcv()})
    provider = CountingProvider(result)
    repo = _make_repo(provider, cache_config)
    request = MarketRequest(("AAPL",), "6mo", "1d", use_cache=False)

    repo.get_market_data(request)
    repo.get_market_data(request)
    assert provider.calls == 2


def test_validation_errors_are_attached(cache_config: CacheConfig) -> None:
    bad = make_ohlcv()
    bad.loc[bad.index[0], "close"] = np.nan
    result = MarketResult(provider="fake", status=MarketStatus.OK, data={"AAPL": bad})
    repo = _make_repo(CountingProvider(result), cache_config)

    returned = repo.get_market_data(MarketRequest(("AAPL",), "6mo", "1d"))
    assert any("AAPL" in message for message in returned.errors)
    assert "validation" in returned.metadata


def test_error_result_is_not_cached(cache_config: CacheConfig) -> None:
    result = MarketResult.error("fake", "kaputt")
    provider = CountingProvider(result)
    repo = _make_repo(provider, cache_config)
    request = MarketRequest(("AAPL",), "6mo", "1d")

    repo.get_market_data(request)
    repo.get_market_data(request)
    assert provider.calls == 2  # ERROR-Ergebnisse werden nicht gecacht
