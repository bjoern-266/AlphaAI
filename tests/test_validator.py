"""Tests für den Marktdaten-Validator."""

from __future__ import annotations

import numpy as np
import pandas as pd

from data.validator import IssueCode, MarketDataValidator, Severity
from tests.helpers import make_ohlcv


def test_valid_frame_has_no_errors() -> None:
    validator = MarketDataValidator()
    report = validator.validate_frame("AAPL", make_ohlcv(), "1d")
    assert report.is_valid is True
    assert report.errors == []


def test_detects_nan() -> None:
    frame = make_ohlcv()
    frame.loc[frame.index[0], "close"] = np.nan
    report = MarketDataValidator().validate_frame("AAPL", frame, "1d")
    assert any(i.code is IssueCode.NAN for i in report.errors)
    assert report.is_valid is False


def test_detects_negative_price() -> None:
    frame = make_ohlcv()
    frame.loc[frame.index[0], "low"] = -5.0
    report = MarketDataValidator().validate_frame("AAPL", frame, "1d")
    assert any(i.code is IssueCode.NEGATIVE_PRICE for i in report.errors)


def test_detects_duplicate_timestamps() -> None:
    frame = make_ohlcv(rows=3)
    dup_index = pd.DatetimeIndex([frame.index[0], frame.index[0], frame.index[2]])
    frame.index = dup_index
    report = MarketDataValidator().validate_frame("AAPL", frame, "1d")
    assert any(i.code is IssueCode.DUPLICATE_TIMESTAMP for i in report.errors)


def test_detects_missing_candle_as_warning() -> None:
    # Tageslücke: 01-01, 01-02, dann Sprung auf 01-10.
    index = pd.DatetimeIndex(["2024-01-01", "2024-01-02", "2024-01-10"])
    frame = make_ohlcv(rows=3)
    frame.index = index
    report = MarketDataValidator().validate_frame("AAPL", frame, "1d")
    gaps = [i for i in report.issues if i.code is IssueCode.MISSING_CANDLE]
    assert len(gaps) == 1
    assert gaps[0].severity is Severity.WARNING
    # Warnung allein macht das Ergebnis nicht ungültig.
    assert report.is_valid is True


def test_invalid_symbol_format() -> None:
    validator = MarketDataValidator()
    assert validator.validate_symbol("AAPL") is None
    issue = validator.validate_symbol("bad symbol!")
    assert issue is not None
    assert issue.code is IssueCode.INVALID_SYMBOL


def test_empty_frame_is_error() -> None:
    empty = pd.DataFrame(columns=["open", "high", "low", "close", "adj_close", "volume"])
    report = MarketDataValidator().validate_frame("AAPL", empty, "1d")
    assert any(i.code is IssueCode.EMPTY for i in report.errors)
