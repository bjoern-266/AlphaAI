"""Tests der System-Status-Ableitung (nur Ablesen von Vorhandensein)."""

from __future__ import annotations

from dashboard.state import SystemStatus
from dashboard.status import module_status, status_item, status_tone
from models.dashboard import (
    TONE_DANGER,
    TONE_INFO,
    TONE_NEUTRAL,
    TONE_SUCCESS,
    TONE_WARNING,
)


def test_module_status_offline_when_absent():
    assert module_status(present=False) is SystemStatus.OFFLINE


def test_module_status_degraded_when_invalid():
    assert module_status(present=True, valid=False) is SystemStatus.DEGRADED


def test_module_status_no_data_when_empty():
    assert module_status(present=True, valid=True, has_data=False) is SystemStatus.NO_DATA


def test_module_status_online():
    assert module_status(present=True, valid=True, has_data=True) is SystemStatus.ONLINE


def test_status_tone_online():
    assert status_tone(SystemStatus.ONLINE) == TONE_SUCCESS


def test_status_tone_offline():
    assert status_tone(SystemStatus.OFFLINE) == TONE_DANGER


def test_status_tone_no_data():
    assert status_tone(SystemStatus.NO_DATA) == TONE_WARNING


def test_status_tone_degraded():
    assert status_tone(SystemStatus.DEGRADED) == TONE_INFO


def test_status_tone_unknown_neutral():
    class _Fake:
        pass

    assert status_tone(_Fake()) == TONE_NEUTRAL  # type: ignore[arg-type]


def test_status_item_builds_from_status():
    item = status_item("Engine", SystemStatus.ONLINE)
    assert item.name == "Engine"
    assert item.status == "online"
    assert item.tone == TONE_SUCCESS


def test_status_item_offline():
    item = status_item("Data", SystemStatus.OFFLINE)
    assert item.status == "offline"
    assert item.tone == TONE_DANGER


def test_absent_takes_priority_over_invalid():
    # Fehlt der Report ganz, ist er offline (nicht nur degraded).
    assert module_status(present=False, valid=False, has_data=False) is SystemStatus.OFFLINE
