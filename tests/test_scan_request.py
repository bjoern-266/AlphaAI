"""Tests für ScanRequest und build_scan_request."""

from __future__ import annotations

import pytest

from core.config import load_settings
from scanner.scan_request import (
    InvalidScanRequestError,
    ScanRequest,
    build_scan_request,
)


def test_symbols_are_normalized_and_deduplicated() -> None:
    request = ScanRequest(market="us", symbols=(" aapl ", "AAPL", "msft"))
    assert request.symbols == ("AAPL", "MSFT")


def test_requires_universe_or_symbols() -> None:
    with pytest.raises(InvalidScanRequestError):
        ScanRequest(market="us")


def test_universe_only_is_valid() -> None:
    request = ScanRequest(market="dax", universe="dax")
    assert request.universe == "dax"
    assert request.symbols == ()


def test_empty_market_raises() -> None:
    with pytest.raises(InvalidScanRequestError):
        ScanRequest(market="  ", universe="dax")


def test_build_scan_request_uses_config_defaults() -> None:
    settings = load_settings()
    request = build_scan_request(settings, market="dax", universe="dax")
    assert request.requested_features == settings.scanner.requested_features
    assert request.max_workers == settings.scanner.max_workers


def test_build_scan_request_overrides() -> None:
    settings = load_settings()
    request = build_scan_request(
        settings,
        market="us",
        symbols=["AAPL"],
        requested_features=["indicators"],
        max_workers=2,
    )
    assert request.requested_features == ("indicators",)
    assert request.max_workers == 2
