"""Tests des Systemdienstes (Version/Status) (Sprint 17)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from application.services import SystemService
from models.application import ReportKind, ServiceInfo
from tests.application_helpers import make_store


def _clock_at(moment: datetime):
    return lambda: moment


def test_version_contains_service_fields() -> None:
    store = make_store(populate=False)
    service = SystemService(store, ServiceInfo(name="AlphaAI", version="1.2.3"))
    version = service.version()
    assert version["name"] == "AlphaAI"
    assert version["version"] == "1.2.3"


def test_version_has_api_version() -> None:
    store = make_store(populate=False)
    service = SystemService(store, ServiceInfo(api_version="v2"))
    assert service.version()["api_version"] == "v2"


def test_uptime_increases_with_clock() -> None:
    start = datetime(2026, 7, 12, 10, 0, tzinfo=UTC)
    later = start + timedelta(seconds=120)
    service = SystemService(make_store(populate=False), started_at=start, clock=_clock_at(later))
    assert service.version()["uptime_seconds"] == 120


def test_uptime_never_negative() -> None:
    start = datetime(2026, 7, 12, 10, 0, tzinfo=UTC)
    earlier = start - timedelta(seconds=60)
    service = SystemService(make_store(populate=False), started_at=start, clock=_clock_at(earlier))
    assert service.version()["uptime_seconds"] == 0


def test_status_reports_stored_counts() -> None:
    service = SystemService(make_store())
    status = service.status()
    assert status["stored_reports"]["operations"] == 1
    assert status["stored_reports"]["opportunities"] == 1


def test_status_includes_service() -> None:
    service = SystemService(make_store(), ServiceInfo(name="AlphaAI"))
    assert service.status()["service"]["name"] == "AlphaAI"


def test_status_includes_system_state_when_operations_present() -> None:
    service = SystemService(make_store())
    assert service.status()["system_state"]["health"] == "ok"


def test_status_system_state_none_without_operations() -> None:
    service = SystemService(make_store(populate=False))
    assert service.status()["system_state"] is None


def test_status_last_scan_at() -> None:
    service = SystemService(make_store())
    assert service.status()["last_scan_at"] == "2026-07-12T14:00:00+00:00"


def test_status_counts_zero_when_empty() -> None:
    service = SystemService(make_store(populate=False))
    counts = service.status()["stored_reports"]
    assert all(value == 0 for value in counts.values())


def test_service_info_started_at_set() -> None:
    start = datetime(2026, 7, 12, 10, 0, tzinfo=UTC)
    service = SystemService(make_store(populate=False), started_at=start, clock=_clock_at(start))
    assert service.service_info().started_at == start


def test_all_report_kinds_present_in_counts() -> None:
    service = SystemService(make_store())
    counts = service.status()["stored_reports"]
    for kind in ReportKind:
        assert kind.value in counts
