"""Tests für die MarketDataEngine."""

from __future__ import annotations

from core.config import load_settings
from data.cache import TTLCache
from data.market_data_engine import MarketDataEngine
from data.market_request import MarketRequest
from data.market_result import MarketResult, MarketStatus
from data.universe import Universe
from data.validator import MarketDataValidator
from providers.base_provider import BaseProvider
from repositories.market_repository import MarketRepository
from tests.helpers import FakeClock, make_ohlcv


class EchoProvider(BaseProvider):
    """Provider-Attrappe, die die empfangene Anfrage in den Metadaten spiegelt."""

    name = "echo"

    def __init__(self) -> None:
        self.last_request: MarketRequest | None = None

    def fetch(self, request: MarketRequest) -> MarketResult:
        self.last_request = request
        data = {symbol: make_ohlcv() for symbol in request.symbols}
        return MarketResult(
            provider=self.name,
            status=MarketStatus.OK,
            data=data,
            metadata={
                "timeframe": request.timeframe,
                "interval": request.interval,
                "market": request.market,
            },
        )


def _build_engine(provider: EchoProvider, resolver=None) -> MarketDataEngine:
    settings = load_settings()
    cache = TTLCache(settings.data.cache, clock=FakeClock())
    repo = MarketRepository(provider, cache, MarketDataValidator())
    return MarketDataEngine(repo, settings, universe_resolver=resolver)


def test_get_symbols_applies_config_defaults() -> None:
    provider = EchoProvider()
    engine = _build_engine(provider)
    settings = load_settings()

    result = engine.get_symbols(["AAPL"])
    assert provider.last_request is not None
    assert provider.last_request.timeframe == settings.data.default_timeframe
    assert provider.last_request.interval == settings.data.default_interval
    assert result.is_ok


def test_get_symbols_overrides_defaults() -> None:
    provider = EchoProvider()
    engine = _build_engine(provider)
    engine.get_symbols(["AAPL"], timeframe="1y", interval="1h")
    assert provider.last_request.timeframe == "1y"
    assert provider.last_request.interval == "1h"


def test_get_universe_resolves_symbols() -> None:
    provider = EchoProvider()
    universe = Universe(
        key="mini",
        name="Mini",
        region="US",
        suffix="",
        complete=False,
        description="Testuniversum",
        base_symbols=("AAPL", "MSFT"),
    )
    engine = _build_engine(provider, resolver=lambda key: universe)

    result = engine.get_universe("mini")
    assert sorted(result.symbols) == ["AAPL", "MSFT"]
    assert provider.last_request.market == "mini"


def test_get_universe_applies_suffix() -> None:
    provider = EchoProvider()
    universe = Universe(
        key="dax",
        name="DAX",
        region="DE",
        suffix=".DE",
        complete=True,
        description="",
        base_symbols=("SAP", "BMW"),
    )
    engine = _build_engine(provider, resolver=lambda key: universe)
    engine.get_universe("dax")
    assert set(provider.last_request.symbols) == {"SAP.DE", "BMW.DE"}
