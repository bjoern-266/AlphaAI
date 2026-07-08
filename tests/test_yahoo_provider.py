"""Tests für den Yahoo-Provider (mit injizierter Download-Attrappe)."""

from __future__ import annotations

import pandas as pd

from data.market_request import MarketRequest
from data.market_result import COL_ADJ_CLOSE, COL_CLOSE, OHLCV_COLUMNS, MarketStatus
from providers.yahoo_provider import YahooProvider
from tests.helpers import make_yahoo_raw


def test_fetch_normalizes_columns() -> None:
    provider = YahooProvider(download_fn=lambda s, t, i: make_yahoo_raw())
    result = provider.fetch(MarketRequest(("AAPL",), "6mo", "1d"))

    assert result.status is MarketStatus.OK
    frame = result.frame("AAPL")
    assert frame is not None
    assert list(frame.columns) == list(OHLCV_COLUMNS)
    assert isinstance(frame.index, pd.DatetimeIndex)


def test_fetch_multiple_symbols() -> None:
    provider = YahooProvider(download_fn=lambda s, t, i: make_yahoo_raw())
    result = provider.fetch(MarketRequest(("AAPL", "MSFT"), "6mo", "1d"))
    assert result.status is MarketStatus.OK
    assert sorted(result.symbols) == ["AAPL", "MSFT"]
    assert result.metadata["returned_symbols"] == 2


def test_empty_download_yields_empty_status() -> None:
    provider = YahooProvider(download_fn=lambda s, t, i: pd.DataFrame())
    result = provider.fetch(MarketRequest(("AAPL",), "6mo", "1d"))
    assert result.status is MarketStatus.EMPTY
    assert result.symbols == []


def test_download_exception_becomes_error() -> None:
    def boom(symbol: str, timeframe: str, interval: str) -> pd.DataFrame:
        raise ConnectionError("kein Netz")

    provider = YahooProvider(download_fn=boom)
    result = provider.fetch(MarketRequest(("AAPL",), "6mo", "1d"))
    assert result.status is MarketStatus.ERROR
    assert any("AAPL" in message for message in result.errors)


def test_partial_when_one_symbol_fails() -> None:
    def sometimes(symbol: str, timeframe: str, interval: str) -> pd.DataFrame:
        if symbol == "BAD":
            return pd.DataFrame()
        return make_yahoo_raw()

    provider = YahooProvider(download_fn=sometimes)
    result = provider.fetch(MarketRequest(("AAPL", "BAD"), "6mo", "1d"))
    assert result.status is MarketStatus.PARTIAL
    assert result.symbols == ["AAPL"]


def test_multiindex_columns_are_flattened() -> None:
    raw = make_yahoo_raw()
    raw.columns = pd.MultiIndex.from_product([raw.columns, ["AAPL"]])
    provider = YahooProvider(download_fn=lambda s, t, i: raw)
    result = provider.fetch(MarketRequest(("AAPL",), "6mo", "1d"))
    frame = result.frame("AAPL")
    assert frame is not None
    # Adj Close (10.4+i) unterscheidet sich hier von Close (10.5+i).
    assert not frame[COL_ADJ_CLOSE].equals(frame[COL_CLOSE])
