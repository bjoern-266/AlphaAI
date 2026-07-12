"""Tests des Hintergrunddienstes inkl. Recovery (Sprint 17)."""

from __future__ import annotations

from datetime import UTC, datetime

from application.repositories import ReportStore
from application.services import BackgroundService
from application.services.background_service import TickResult
from models.application import ReportKind
from tests.application_helpers import FakeOperations

_NOW = datetime(2026, 7, 12, 14, 0, tzinfo=UTC)


def _service(**kwargs) -> tuple[BackgroundService, ReportStore, FakeOperations]:
    store = ReportStore(":memory:")
    ops = kwargs.pop("operations", FakeOperations())
    service = BackgroundService(ops, store, clock=lambda: _NOW, **kwargs)
    return service, store, ops


def test_start_sets_started_flag() -> None:
    service, _, _ = _service()
    service.start(_NOW)
    assert service.started is True


def test_start_beats_heartbeat() -> None:
    service, _, ops = _service()
    service.start(_NOW)
    assert ops.beats == 1


def test_start_persists_operations() -> None:
    service, store, _ = _service()
    service.start(_NOW)
    assert store.latest(ReportKind.OPERATIONS.value) is not None


def test_tick_persists_report_version() -> None:
    service, store, _ = _service()
    service.start(_NOW)
    assert store.latest(ReportKind.OPERATIONS.value).report_version == 7


def test_tick_returns_result() -> None:
    service, _, _ = _service()
    result = service.start(_NOW)
    assert isinstance(result, TickResult)
    assert result.ok is True
    assert ReportKind.OPERATIONS.value in result.stored_kinds


def test_tick_count_increases() -> None:
    service, _, _ = _service()
    service.start(_NOW)
    service.tick(_NOW)
    assert service.tick_count == 2


def test_report_sources_persisted() -> None:
    service, store, _ = _service(
        report_sources={ReportKind.ANALYTICS.value: lambda: {"result": {"trade_count": 3}}}
    )
    service.start(_NOW)
    assert store.latest(ReportKind.ANALYTICS.value).payload["result"]["trade_count"] == 3


def test_report_source_none_skipped() -> None:
    service, store, _ = _service(report_sources={ReportKind.ANALYTICS.value: lambda: None})
    result = service.start(_NOW)
    assert ReportKind.ANALYTICS.value not in result.stored_kinds
    assert store.latest(ReportKind.ANALYTICS.value) is None


def test_recovery_operations_failure_does_not_raise() -> None:
    service, store, _ = _service(operations=FakeOperations(fail=True))
    result = service.start(_NOW)
    assert result.ok is False
    assert ReportKind.OPERATIONS.value in result.errors


def test_recovery_continues_after_operations_failure() -> None:
    service, store, _ = _service(
        operations=FakeOperations(fail=True),
        report_sources={ReportKind.ANALYTICS.value: lambda: {"ok": True}},
    )
    result = service.start(_NOW)
    # Trotz Operations-Fehler wird die Analytics-Quelle gespeichert.
    assert ReportKind.ANALYTICS.value in result.stored_kinds


def test_recovery_source_failure_isolated() -> None:
    def boom() -> dict:
        raise RuntimeError("Quelle kaputt")

    service, store, _ = _service(
        report_sources={
            ReportKind.ANALYTICS.value: boom,
            ReportKind.DISCOVERY.value: lambda: {"ok": True},
        }
    )
    result = service.start(_NOW)
    assert ReportKind.ANALYTICS.value in result.errors
    assert ReportKind.DISCOVERY.value in result.stored_kinds


def test_error_count_accumulates() -> None:
    service, _, _ = _service(operations=FakeOperations(fail=True))
    service.start(_NOW)
    service.tick(_NOW)
    assert service.error_count == 2


def test_service_survives_many_failures() -> None:
    service, _, _ = _service(operations=FakeOperations(fail=True))
    for _ in range(10):
        result = service.tick(_NOW)
        assert result.ok is False
    # Der Dienst läuft weiter (keine Ausnahme, Zähler steigt).
    assert service.error_count == 10


def test_run_cycles_multiple() -> None:
    service, store, ops = _service()
    results = service.run_cycles(3, start_at=_NOW)
    assert len(results) == 3
    assert ops.ticks == 3


def test_run_cycles_starts_service() -> None:
    service, _, _ = _service()
    service.run_cycles(1, start_at=_NOW)
    assert service.started is True


def test_run_cycles_zero() -> None:
    service, _, _ = _service()
    assert service.run_cycles(0) == ()


def test_tick_result_ok_property() -> None:
    result = TickResult(as_of=_NOW, stored_kinds=("operations",), errors={})
    assert result.ok is True
    assert TickResult(as_of=_NOW, errors={"x": "y"}).ok is False


def test_non_dict_report_wrapped() -> None:
    service, store, _ = _service(report_sources={ReportKind.ANALYTICS.value: lambda: [1, 2, 3]})
    service.start(_NOW)
    payload = store.latest(ReportKind.ANALYTICS.value).payload
    assert payload == {"value": [1, 2, 3]}


def test_started_false_initially() -> None:
    service, _, _ = _service()
    assert service.started is False


def test_persisted_created_at_matches_clock() -> None:
    service, store, _ = _service()
    service.start(_NOW)
    assert store.latest(ReportKind.OPERATIONS.value).created_at == _NOW


def test_multiple_sources_all_stored() -> None:
    service, store, _ = _service(
        report_sources={
            ReportKind.ANALYTICS.value: lambda: {"a": 1},
            ReportKind.DISCOVERY.value: lambda: {"d": 1},
            ReportKind.BACKTESTING.value: lambda: {"b": 1},
        }
    )
    result = service.start(_NOW)
    for kind in (ReportKind.ANALYTICS, ReportKind.DISCOVERY, ReportKind.BACKTESTING):
        assert kind.value in result.stored_kinds
