"""Tests des Heartbeats (Lebendigkeit)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from operations.heartbeat import build_heartbeat

_NOW = datetime(2024, 6, 3, 12, 0, tzinfo=UTC)


def test_no_beat_is_dead():
    beat = build_heartbeat(None, _NOW, 60)
    assert beat.alive is False
    assert beat.age_seconds is None


def test_recent_beat_alive():
    beat = build_heartbeat(_NOW - timedelta(seconds=30), _NOW, 60)
    assert beat.alive is True
    assert beat.age_seconds == 30


def test_beat_at_boundary_alive():
    beat = build_heartbeat(_NOW - timedelta(seconds=120), _NOW, 60)
    assert beat.alive is True  # genau doppeltes Intervall


def test_old_beat_dead():
    beat = build_heartbeat(_NOW - timedelta(seconds=121), _NOW, 60)
    assert beat.alive is False


def test_age_seconds():
    beat = build_heartbeat(_NOW - timedelta(seconds=45), _NOW, 60)
    assert beat.age_seconds == 45


def test_interval_recorded():
    beat = build_heartbeat(_NOW, _NOW, 90)
    assert beat.interval_seconds == 90


def test_zero_age_alive():
    beat = build_heartbeat(_NOW, _NOW, 60)
    assert beat.alive is True
    assert beat.age_seconds == 0


def test_future_beat_not_alive():
    # Ein Herzschlag „aus der Zukunft" (negatives Alter) gilt nicht als lebendig.
    beat = build_heartbeat(_NOW + timedelta(seconds=10), _NOW, 60)
    assert beat.alive is False


def test_last_beat_recorded():
    last = _NOW - timedelta(seconds=10)
    beat = build_heartbeat(last, _NOW, 60)
    assert beat.last_beat_at == last
