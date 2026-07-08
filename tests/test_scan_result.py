"""Tests für ScanResult und ScanReport."""

from __future__ import annotations

from datetime import UTC, datetime

from scanner.scan_request import ScanRequest
from scanner.scan_result import ScanReport, ScanResult, ScanStatus
from tests.helpers import make_ohlcv


def _result(ticker: str, status: ScanStatus) -> ScanResult:
    return ScanResult(
        ticker=ticker,
        provider="yahoo",
        market="us",
        timeframe="6mo",
        timestamp=datetime.now(UTC),
        status=status,
        raw_market_data=make_ohlcv() if status is ScanStatus.OK else None,
    )


def test_prepared_analysis_fields_are_empty() -> None:
    result = _result("AAPL", ScanStatus.OK)
    assert result.indicators == {}
    assert result.patterns == []
    assert result.score is None
    assert result.risk is None
    assert result.recommendation is None


def test_has_data_and_is_ok() -> None:
    ok = _result("AAPL", ScanStatus.OK)
    assert ok.has_data is True
    assert ok.is_ok is True
    empty = _result("XXX", ScanStatus.NO_DATA)
    assert empty.has_data is False
    assert empty.is_ok is False


def test_report_partitions_results() -> None:
    request = ScanRequest(market="us", symbols=("AAPL", "BBB", "CCC"))
    report = ScanReport(
        request=request,
        results=[
            _result("AAPL", ScanStatus.OK),
            _result("BBB", ScanStatus.NO_DATA),
            _result("CCC", ScanStatus.ERROR),
        ],
    )
    assert report.symbol_count == 3
    assert [r.ticker for r in report.ok_results] == ["AAPL"]
    assert [r.ticker for r in report.no_data_results] == ["BBB"]
    assert [r.ticker for r in report.error_results] == ["CCC"]
