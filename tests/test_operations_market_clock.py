"""Tests der Marktuhr (Phasen, Countdown, Sommer-/Winterzeit, nächste Öffnung)."""

from __future__ import annotations

from datetime import UTC, datetime

from operations.market_clock import (
    build_market_clock,
    compute_market_state,
    next_open_at,
)
from operations.market_sessions import build_session

_EUROPE = build_session(
    "europe",
    {
        "title": "Europa",
        "timezone": "Europe/Berlin",
        "phases": [
            ["pre_market", "07:30", False],
            ["open", "09:00", True],
            ["afternoon", "12:00", True],
            ["close", "17:30", False],
        ],
    },
)
_US = build_session(
    "us",
    {
        "title": "USA",
        "timezone": "America/New_York",
        "phases": [
            ["pre_market", "04:00", False],
            ["opening_bell", "09:30", True],
            ["first_hour", "10:30", True],
            ["afternoon", "13:00", True],
            ["close", "16:00", False],
        ],
    },
)


def test_europe_open_phase_summer():
    # 07:05 UTC = 09:05 Berlin (CEST) -> open.
    now = datetime(2024, 6, 3, 7, 5, tzinfo=UTC)
    state = compute_market_state(_EUROPE, now)
    assert state.phase == "open"
    assert state.is_open is True
    assert state.next_phase == "afternoon"


def test_europe_countdown_to_next_phase():
    now = datetime(2024, 6, 3, 7, 5, tzinfo=UTC)  # 09:05 Berlin
    state = compute_market_state(_EUROPE, now)
    # nächste Phase 12:00 Berlin = 10:00 UTC -> 2h55m.
    assert state.seconds_to_next == (2 * 3600 + 55 * 60)


def test_europe_before_first_phase_is_closed():
    now = datetime(2024, 6, 3, 5, 0, tzinfo=UTC)  # 07:00 Berlin, vor pre_market
    state = compute_market_state(_EUROPE, now)
    assert state.phase == "close"  # letzte Phase von gestern
    assert state.is_open is False
    assert state.next_phase == "pre_market"


def test_europe_after_close():
    now = datetime(2024, 6, 3, 16, 0, tzinfo=UTC)  # 18:00 Berlin, nach close
    state = compute_market_state(_EUROPE, now)
    assert state.phase == "close"
    assert state.is_open is False
    # nächste Phase ist pre_market am Folgetag.
    assert state.next_phase == "pre_market"


def test_us_opening_bell_summer():
    now = datetime(2024, 6, 3, 13, 35, tzinfo=UTC)  # 09:35 NY (EDT)
    state = compute_market_state(_US, now)
    assert state.phase == "opening_bell"
    assert state.is_open is True


def test_us_opening_bell_winter_same_local_time():
    # 14:35 UTC im Winter = 09:35 NY (EST) -> gleiche lokale Zeit, andere UTC.
    now = datetime(2024, 1, 15, 14, 35, tzinfo=UTC)
    state = compute_market_state(_US, now)
    assert state.phase == "opening_bell"
    assert state.is_open is True


def test_dst_shifts_utc_boundary():
    # Sommer: 13:30 UTC ist Opening Bell; Winter: 13:30 UTC ist noch pre_market.
    summer = compute_market_state(_US, datetime(2024, 6, 3, 13, 35, tzinfo=UTC))
    winter = compute_market_state(_US, datetime(2024, 1, 15, 13, 35, tzinfo=UTC))
    assert summer.phase == "opening_bell"
    assert winter.phase == "pre_market"


def test_next_change_at_is_utc():
    now = datetime(2024, 6, 3, 13, 35, tzinfo=UTC)
    state = compute_market_state(_US, now)
    assert state.next_change_at is not None
    assert state.next_change_at.tzinfo is not None


def test_next_open_at_when_closed():
    now = datetime(2024, 6, 3, 5, 0, tzinfo=UTC)  # Europa geschlossen (07:00 Berlin)
    opens = next_open_at(_EUROPE, now)
    # nächste offene Phase = open 09:00 Berlin = 07:00 UTC.
    assert opens == datetime(2024, 6, 3, 7, 0, tzinfo=UTC)


def test_next_open_at_when_open_returns_future():
    now = datetime(2024, 6, 3, 7, 5, tzinfo=UTC)  # Europa open
    opens = next_open_at(_EUROPE, now)
    # nächste offene Phase = afternoon (12:00 Berlin) = 10:00 UTC.
    assert opens == datetime(2024, 6, 3, 10, 0, tzinfo=UTC)


def test_next_open_at_wraps_to_next_day():
    now = datetime(2024, 6, 3, 16, 0, tzinfo=UTC)  # 18:00 Berlin, nach close
    opens = next_open_at(_EUROPE, now)
    assert opens.date() == datetime(2024, 6, 4, tzinfo=UTC).date()


def test_build_market_clock_states():
    now = datetime(2024, 6, 3, 13, 35, tzinfo=UTC)
    clock = build_market_clock([_EUROPE, _US], now)
    assert len(clock.markets) == 2
    assert "us" in clock.open_markets  # US Opening Bell
    assert "europe" in clock.open_markets  # 15:35 Berlin afternoon


def test_build_market_clock_next_open_market():
    # Nachts (alle geschlossen): der als nächstes öffnende Markt wird bestimmt.
    now = datetime(2024, 6, 3, 3, 0, tzinfo=UTC)  # 05:00 Berlin / 23:00 Vortag NY
    clock = build_market_clock([_EUROPE, _US], now)
    assert clock.next_open_market in {"europe", "us"}
    assert clock.next_open_at is not None


def test_build_market_clock_as_of():
    now = datetime(2024, 6, 3, 13, 35, tzinfo=UTC)
    clock = build_market_clock([_EUROPE], now)
    assert clock.as_of == now


def test_europe_afternoon_open():
    now = datetime(2024, 6, 3, 10, 30, tzinfo=UTC)  # 12:30 Berlin
    state = compute_market_state(_EUROPE, now)
    assert state.phase == "afternoon"
    assert state.is_open is True


def test_seconds_to_next_positive():
    now = datetime(2024, 6, 3, 13, 35, tzinfo=UTC)
    for session in (_EUROPE, _US):
        state = compute_market_state(session, now)
        assert state.seconds_to_next is not None
        assert state.seconds_to_next > 0


def test_us_closed_overnight():
    now = datetime(2024, 6, 3, 2, 0, tzinfo=UTC)  # 22:00 NY Vortag -> nach close
    state = compute_market_state(_US, now)
    assert state.is_open is False


def test_market_state_carries_key_title():
    now = datetime(2024, 6, 3, 13, 35, tzinfo=UTC)
    state = compute_market_state(_US, now)
    assert state.key == "us"
    assert state.title == "USA"
