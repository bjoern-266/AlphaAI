"""Tests für MarketResult."""

from __future__ import annotations

from data.market_result import MarketResult, MarketStatus
from tests.helpers import make_ohlcv


def test_ok_result_reports_symbols() -> None:
    result = MarketResult(
        provider="yahoo",
        status=MarketStatus.OK,
        data={"AAPL": make_ohlcv(), "MSFT": make_ohlcv()},
    )
    assert result.is_ok is True
    assert sorted(result.symbols) == ["AAPL", "MSFT"]


def test_frame_lookup_is_case_insensitive() -> None:
    result = MarketResult(provider="yahoo", status=MarketStatus.OK, data={"AAPL": make_ohlcv()})
    assert result.frame("aapl") is not None
    assert result.frame("UNKNOWN") is None


def test_empty_factory() -> None:
    result = MarketResult.empty("yahoo")
    assert result.status is MarketStatus.EMPTY
    assert result.symbols == []
    assert result.is_ok is False


def test_error_factory_records_message() -> None:
    result = MarketResult.error("yahoo", "Verbindung fehlgeschlagen")
    assert result.status is MarketStatus.ERROR
    assert result.errors == ["Verbindung fehlgeschlagen"]


def test_add_error_appends() -> None:
    result = MarketResult.empty("yahoo")
    result.add_error("Problem")
    assert "Problem" in result.errors
