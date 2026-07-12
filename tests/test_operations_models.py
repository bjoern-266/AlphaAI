"""Tests der Operations-Modelle (unveränderlich, UI-unabhängig)."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from models.operations import (
    Heartbeat,
    JobDefinition,
    JobRun,
    JobStatus,
    MarketClock,
    MarketState,
    OperationReport,
    ScheduledJob,
    SystemHealth,
    SystemState,
)

_T0 = datetime(2024, 1, 1, tzinfo=UTC)


def _market(key="us", is_open=True):
    return MarketState(
        key=key,
        title=key.upper(),
        timezone="America/New_York",
        phase="open",
        is_open=is_open,
        next_phase="close",
        next_change_at=_T0,
        seconds_to_next=3600,
    )


def test_job_status_values():
    assert {s.value for s in JobStatus} == {"pending", "running", "success", "failed", "skipped"}


def test_system_health_values():
    assert {s.value for s in SystemHealth} == {"ok", "degraded", "error"}


def test_market_state_is_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        _market().phase = "x"  # type: ignore[misc]


def test_market_clock_open_closed():
    clock = MarketClock(as_of=_T0, markets=(_market("us", True), _market("europe", False)))
    assert clock.open_markets == ("us",)
    assert clock.closed_markets == ("europe",)


def test_market_clock_get():
    clock = MarketClock(as_of=_T0, markets=(_market("us"),))
    assert clock.get("us").key == "us"
    assert clock.get("nope") is None


def test_job_run_ok_property():
    ok = JobRun(name="a", job_type="discovery", status=JobStatus.SUCCESS)
    failed = JobRun(name="b", job_type="discovery", status=JobStatus.FAILED)
    assert ok.ok is True
    assert failed.ok is False


def test_job_run_defaults():
    run = JobRun(name="a", job_type="discovery", status=JobStatus.PENDING)
    assert run.error == ""
    assert run.duration_seconds is None


def test_scheduled_job_defaults():
    job = ScheduledJob(name="a", job_type="discovery", time="09:00", timezone="UTC")
    assert job.enabled is True


def test_job_definition_defaults():
    definition = JobDefinition(name="discovery")
    assert definition.exclusive is False


def test_heartbeat_defaults():
    beat = Heartbeat(alive=True)
    assert beat.interval_seconds == 60


def test_system_state_defaults():
    state = SystemState()
    assert state.health is SystemHealth.OK
    assert state.scan_count == 0


def test_operation_report_defaults():
    report = OperationReport(as_of=_T0, market_clock=MarketClock(as_of=_T0))
    assert report.valid is True
    assert report.job_history == ()
    assert report.new_opportunities == ()


def test_operation_report_open_markets():
    clock = MarketClock(as_of=_T0, markets=(_market("us", True),))
    report = OperationReport(as_of=_T0, market_clock=clock)
    assert report.open_markets == ("us",)


def test_operation_report_recent_jobs():
    runs = tuple(
        JobRun(name=f"j{i}", job_type="discovery", status=JobStatus.SUCCESS) for i in range(5)
    )
    report = OperationReport(as_of=_T0, market_clock=MarketClock(as_of=_T0), job_history=runs)
    assert len(report.recent_jobs(2)) == 2
    assert report.recent_jobs(0) == ()


def test_operation_report_is_frozen():
    report = OperationReport(as_of=_T0, market_clock=MarketClock(as_of=_T0))
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.valid = False  # type: ignore[misc]


def test_market_clock_defaults():
    clock = MarketClock(as_of=_T0)
    assert clock.markets == ()
    assert clock.next_open_market == ""


def test_heartbeat_is_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        Heartbeat(alive=True).alive = False  # type: ignore[misc]
