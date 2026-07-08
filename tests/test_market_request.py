"""Tests für MarketRequest."""

from __future__ import annotations

import pytest

from data.market_request import InvalidRequestError, MarketRequest, build_request


def test_symbols_are_normalized() -> None:
    request = MarketRequest(symbols=(" aapl ", "msft"), timeframe="6mo", interval="1d")
    assert request.symbols == ("AAPL", "MSFT")


def test_empty_symbols_raise() -> None:
    with pytest.raises(InvalidRequestError):
        MarketRequest(symbols=("  ", ""), timeframe="6mo", interval="1d")


def test_missing_interval_raises() -> None:
    with pytest.raises(InvalidRequestError):
        MarketRequest(symbols=("AAPL",), timeframe="6mo", interval="  ")


def test_is_intraday_detection() -> None:
    assert MarketRequest(("AAPL",), "5d", "5m").is_intraday is True
    assert MarketRequest(("AAPL",), "5d", "1h").is_intraday is True
    assert MarketRequest(("AAPL",), "6mo", "1d").is_intraday is False
    assert MarketRequest(("AAPL",), "1y", "1mo").is_intraday is False


def test_cache_key_is_order_independent() -> None:
    a = MarketRequest(("AAPL", "MSFT"), "6mo", "1d", market="us")
    b = MarketRequest(("MSFT", "AAPL"), "6mo", "1d", market="us")
    assert a.cache_key() == b.cache_key()


def test_cache_key_distinguishes_interval() -> None:
    a = MarketRequest(("AAPL",), "6mo", "1d")
    b = MarketRequest(("AAPL",), "6mo", "1h")
    assert a.cache_key() != b.cache_key()


def test_build_request_from_list() -> None:
    request = build_request(["AAPL"], "1y", "1d", market="us", use_cache=False)
    assert request.symbols == ("AAPL",)
    assert request.use_cache is False
    assert request.market == "us"
