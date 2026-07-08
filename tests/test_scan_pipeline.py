"""Tests für die ScanPipeline (reine Orchestrierung)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from core.config import load_settings
from data.universe import Universe
from scanner.scan_pipeline import ScanPipeline
from scanner.scan_request import ScanRequest
from scanner.scan_result import ScanStatus
from tests.helpers import FakeClock, make_engine, make_yahoo_raw


class DatetimeClock:
    """Deterministische Datetime-Zeitquelle, die pro Aufruf fortschreitet."""

    def __init__(self) -> None:
        self._current = datetime(2024, 1, 1, tzinfo=UTC)

    def __call__(self) -> datetime:
        value = self._current
        self._current += timedelta(seconds=1)
        return value


def _download_dispatch(ok=("AAPL", "MSFT"), empty=(), error=()):
    """Erzeugt eine Download-Funktion mit symbolabhängigem Verhalten."""

    def download(symbol: str, timeframe: str, interval: str) -> pd.DataFrame:
        if symbol in error:
            raise ConnectionError(f"kein Netz für {symbol}")
        if symbol in empty:
            return pd.DataFrame()
        if symbol in ok:
            return make_yahoo_raw()
        return pd.DataFrame()

    return download


def _universe(*symbols: str, suffix: str = "") -> Universe:
    return Universe(
        key="test",
        name="Test",
        region="US",
        suffix=suffix,
        complete=False,
        description="",
        base_symbols=symbols,
    )


def _pipeline(download, resolver=None) -> ScanPipeline:
    settings = load_settings()
    engine = make_engine(download, settings, FakeClock(), universe_resolver=resolver)
    return ScanPipeline(engine, universe_resolver=resolver, now_fn=DatetimeClock())


def test_scan_symbols_ok() -> None:
    pipeline = _pipeline(_download_dispatch(ok=("AAPL", "MSFT")))
    report = pipeline.run(ScanRequest(market="us", symbols=("AAPL", "MSFT")))

    assert report.symbol_count == 2
    assert all(r.status is ScanStatus.OK for r in report.results)
    assert all(r.has_data for r in report.results)
    assert report.statistics.symbol_count == 2


def test_no_data_symbol_maps_to_no_data() -> None:
    pipeline = _pipeline(_download_dispatch(ok=("AAPL",), empty=("XXX",)))
    report = pipeline.run(ScanRequest(market="us", symbols=("AAPL", "XXX")))

    statuses = {r.ticker: r.status for r in report.results}
    assert statuses["AAPL"] is ScanStatus.OK
    assert statuses["XXX"] is ScanStatus.NO_DATA


def test_error_symbol_maps_to_error() -> None:
    pipeline = _pipeline(_download_dispatch(ok=("AAPL",), error=("BAD",)))
    report = pipeline.run(ScanRequest(market="us", symbols=("AAPL", "BAD")))

    error_result = next(r for r in report.results if r.ticker == "BAD")
    assert error_result.status is ScanStatus.ERROR
    assert error_result.error
    assert report.statistics.error_count == 1


def test_universe_symbols_are_resolved_with_suffix() -> None:
    resolver = lambda key: _universe("SAP", "BMW", suffix=".DE")  # noqa: E731
    pipeline = _pipeline(_download_dispatch(ok=("SAP.DE", "BMW.DE")), resolver=resolver)
    report = pipeline.run(ScanRequest(market="dax", universe="dax"))

    assert {r.ticker for r in report.results} == {"SAP.DE", "BMW.DE"}


def test_universe_and_explicit_symbols_merge_deduplicated() -> None:
    resolver = lambda key: _universe("AAPL", "MSFT")  # noqa: E731
    pipeline = _pipeline(_download_dispatch(ok=("AAPL", "MSFT", "TSLA")), resolver=resolver)
    report = pipeline.run(ScanRequest(market="us", universe="us", symbols=("MSFT", "TSLA")))
    tickers = [r.ticker for r in report.results]
    assert tickers == ["AAPL", "MSFT", "TSLA"]  # dedupliziert, Reihenfolge erhalten


def test_cache_hits_on_second_run() -> None:
    settings = load_settings()
    engine = make_engine(_download_dispatch(ok=("AAPL",)), settings, FakeClock())
    pipeline = ScanPipeline(engine, now_fn=DatetimeClock())
    request = ScanRequest(market="us", symbols=("AAPL",), use_cache=True)

    first = pipeline.run(request)
    second = pipeline.run(request)
    assert first.statistics.cache_misses == 1
    assert second.statistics.cache_hits == 1


def test_statistics_capture_provider_and_runtime() -> None:
    pipeline = _pipeline(_download_dispatch(ok=("AAPL",)))
    report = pipeline.run(ScanRequest(market="us", symbols=("AAPL",)))
    assert report.statistics.provider == "yahoo"
    assert report.statistics.runtime_seconds > 0
