"""Tests für den ScannerManager."""

from __future__ import annotations

from core.config import load_settings
from scanner.scan_request import ScanRequest
from scanner.scan_result import ScanReport
from scanner.scanner_manager import ScannerManager


class RecordingEngine:
    """Engine-Attrappe, die ausgeführte Anfragen protokolliert."""

    def __init__(self) -> None:
        self.scanned: list[ScanRequest] = []

    def scan(self, request: ScanRequest) -> ScanReport:
        self.scanned.append(request)
        return ScanReport(request=request, results=[])


def test_scan_all_runs_each_request_sequentially() -> None:
    engine = RecordingEngine()
    manager = ScannerManager(engine, load_settings())  # type: ignore[arg-type]
    requests = [
        ScanRequest(market="us", symbols=("AAPL",)),
        ScanRequest(market="dax", universe="dax"),
    ]
    reports = manager.scan_all(requests)
    assert len(reports) == 2
    assert engine.scanned == requests


def test_build_requests_creates_universe_timeframe_combinations() -> None:
    settings = load_settings()
    manager = ScannerManager(RecordingEngine(), settings)  # type: ignore[arg-type]
    requests = manager.build_requests(
        universes=["dax", "usa"],
        timeframes=["6mo", "1y"],
    )
    assert len(requests) == 4
    combos = {(r.universe, r.timeframe) for r in requests}
    assert combos == {("dax", "6mo"), ("dax", "1y"), ("usa", "6mo"), ("usa", "1y")}


def test_build_requests_applies_config_defaults() -> None:
    settings = load_settings()
    manager = ScannerManager(RecordingEngine(), settings)  # type: ignore[arg-type]
    requests = manager.build_requests(universes=["dax"], timeframes=["6mo"])
    assert requests[0].max_workers == settings.scanner.max_workers
    assert requests[0].requested_features == settings.scanner.requested_features
