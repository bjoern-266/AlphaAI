"""Tests der Marktsitzungen (Phasen, Zeiten, Zeitzonen, Validierung)."""

from __future__ import annotations

import pytest

from operations.market_sessions import (
    MarketSessionError,
    build_session,
    load_sessions,
    parse_time,
)


def test_parse_time():
    assert parse_time("00:00") == 0
    assert parse_time("09:30") == 9 * 60 + 30
    assert parse_time("23:59") == 23 * 60 + 59


def test_parse_time_invalid_format():
    with pytest.raises(MarketSessionError):
        parse_time("9-30")


def test_parse_time_non_numeric():
    with pytest.raises(MarketSessionError):
        parse_time("ab:cd")


def test_parse_time_out_of_range():
    with pytest.raises(MarketSessionError):
        parse_time("25:00")


def test_parse_time_minute_out_of_range():
    with pytest.raises(MarketSessionError):
        parse_time("10:70")


def _config():
    return {
        "title": "Europa",
        "timezone": "Europe/Berlin",
        "phases": [["open", "09:00", True], ["pre", "07:30", False], ["close", "17:30", False]],
    }


def test_build_session_sorts_phases():
    session = build_session("europe", _config())
    assert [p.name for p in session.phases] == ["pre", "open", "close"]


def test_build_session_fields():
    session = build_session("europe", _config())
    assert session.key == "europe"
    assert session.title == "Europa"
    assert session.timezone == "Europe/Berlin"


def test_build_session_phase_open_flag():
    session = build_session("europe", _config())
    open_phase = next(p for p in session.phases if p.name == "open")
    assert open_phase.is_open is True


def test_build_session_invalid_timezone():
    config = _config()
    config["timezone"] = "Mars/Olympus"
    with pytest.raises(MarketSessionError):
        build_session("x", config)


def test_build_session_no_phases():
    with pytest.raises(MarketSessionError):
        build_session("x", {"timezone": "UTC", "phases": []})


def test_build_session_bad_phase_shape():
    with pytest.raises(MarketSessionError):
        build_session("x", {"timezone": "UTC", "phases": [["open", "09:00"]]})


def test_build_session_bad_phase_time():
    with pytest.raises(MarketSessionError):
        build_session("x", {"timezone": "UTC", "phases": [["open", "99:00", True]]})


def test_load_sessions():
    markets = {
        "europe": _config(),
        "us": {"timezone": "America/New_York", "phases": [["open", "09:30", True]]},
    }
    sessions = load_sessions(markets)
    assert {s.key for s in sessions} == {"europe", "us"}


def test_load_sessions_empty():
    with pytest.raises(MarketSessionError):
        load_sessions({})


def test_default_timezone_utc():
    session = build_session("x", {"phases": [["open", "09:00", True]]})
    assert session.timezone == "UTC"


def test_default_title_is_key():
    session = build_session("mykey", {"timezone": "UTC", "phases": [["open", "09:00", True]]})
    assert session.title == "mykey"


def test_summer_and_winter_timezone_valid():
    # Eine DST-behaftete Zeitzone ist gültig (Sommer-/Winterzeit inklusive).
    session = build_session(
        "us", {"timezone": "America/New_York", "phases": [["open", "09:30", True]]}
    )
    assert session.timezone == "America/New_York"
