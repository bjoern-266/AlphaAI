"""Tests für die Repository-Factory (Composition Root)."""

from __future__ import annotations

from core.config import load_settings
from data.market_request import MarketRequest
from data.market_result import MarketResult, MarketStatus
from providers.base_provider import BaseProvider
from repositories.market_repository import MarketRepository
from repositories.repository_factory import build_repository
from tests.helpers import FakeClock, make_ohlcv


class DummyProvider(BaseProvider):
    """Minimaler Provider für den Factory-Test."""

    name = "dummy"

    def fetch(self, request: MarketRequest) -> MarketResult:
        return MarketResult(
            provider=self.name,
            status=MarketStatus.OK,
            data={symbol: make_ohlcv() for symbol in request.symbols},
        )


def test_build_repository_with_default_provider() -> None:
    settings = load_settings()
    repo = build_repository(settings)
    assert isinstance(repo, MarketRepository)


def test_build_repository_uses_injected_provider() -> None:
    settings = load_settings()
    repo = build_repository(settings, provider=DummyProvider(), clock=FakeClock())
    result = repo.get_market_data(MarketRequest(("AAPL",), "6mo", "1d"))
    assert result.provider == "dummy"
    assert result.is_ok
