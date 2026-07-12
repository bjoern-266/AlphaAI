"""Tests der Health-Ableitung (OK/DEGRADED/ERROR)."""

from __future__ import annotations

from datetime import UTC, datetime

from models.operations import SystemHealth
from operations.health import assess_health
from operations.heartbeat import build_heartbeat
from operations.system_state import build_system_state

_NOW = datetime(2024, 6, 3, 12, 0, tzinfo=UTC)
_ALIVE = build_heartbeat(_NOW, _NOW, 60)
_DEAD = build_heartbeat(None, _NOW, 60)


def test_ok_no_errors():
    assert assess_health(0, 5, _ALIVE) is SystemHealth.OK


def test_error_when_heartbeat_dead():
    assert assess_health(0, 5, _DEAD) is SystemHealth.ERROR


def test_degraded_errors_no_scans():
    assert assess_health(2, 0, _ALIVE) is SystemHealth.DEGRADED


def test_degraded_high_error_ratio():
    # 4 Fehler / (4+4) = 0.5 > 0.3.
    assert assess_health(4, 4, _ALIVE) is SystemHealth.DEGRADED


def test_ok_low_error_ratio():
    # 1 Fehler / (1+9) = 0.1 <= 0.3.
    assert assess_health(1, 9, _ALIVE) is SystemHealth.OK


def test_ok_without_heartbeat():
    assert assess_health(0, 3, None) is SystemHealth.OK


def test_custom_degraded_ratio():
    assert assess_health(1, 9, _ALIVE, degraded_ratio=0.05) is SystemHealth.DEGRADED


def test_dead_heartbeat_overrides_ok():
    assert assess_health(0, 100, _DEAD) is SystemHealth.ERROR


def test_no_activity_is_ok():
    assert assess_health(0, 0, _ALIVE) is SystemHealth.OK


def test_build_system_state_health():
    state = build_system_state(_ALIVE, running_job="d", queue_size=1, scan_count=3, error_count=0)
    assert state.health is SystemHealth.OK
    assert state.running_job == "d"
    assert state.queue_size == 1
    assert state.scan_count == 3


def test_build_system_state_degraded():
    state = build_system_state(_ALIVE, running_job=None, queue_size=0, scan_count=1, error_count=4)
    assert state.health is SystemHealth.DEGRADED


def test_build_system_state_error_on_dead_heartbeat():
    state = build_system_state(_DEAD, running_job=None, queue_size=0, scan_count=5, error_count=0)
    assert state.health is SystemHealth.ERROR
