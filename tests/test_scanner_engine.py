"""Tests für die ScannerEngine."""

from __future__ import annotations

from datetime import UTC

from scanner.scan_request import ScanRequest
from scanner.scan_result import ScanReport, ScanResult
from scanner.scanner_engine import ScannerEngine


class StubPipeline:
    """Pipeline-Attrappe, die einen festen Report liefert und Aufrufe merkt."""

    def __init__(self, report: ScanReport) -> None:
        self._report = report
        self.received: ScanRequest | None = None

    def run(self, request: ScanRequest) -> ScanReport:
        self.received = request
        return self._report


def test_engine_delegates_to_pipeline() -> None:
    request = ScanRequest(market="us", symbols=("AAPL",))
    report = ScanReport(request=request, results=[])
    pipeline = StubPipeline(report)
    engine = ScannerEngine(pipeline)  # type: ignore[arg-type]

    returned = engine.scan(request)
    assert returned is report
    assert pipeline.received is request


def test_engine_returns_report_with_results() -> None:
    from datetime import datetime

    from scanner.scan_result import ScanStatus

    request = ScanRequest(market="us", symbols=("AAPL",))
    result = ScanResult(
        ticker="AAPL",
        provider="yahoo",
        market="us",
        timeframe="6mo",
        timestamp=datetime.now(UTC),
        status=ScanStatus.OK,
    )
    report = ScanReport(request=request, results=[result])
    engine = ScannerEngine(StubPipeline(report))  # type: ignore[arg-type]

    returned = engine.scan(request)
    assert returned.symbol_count == 1
