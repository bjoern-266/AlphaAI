"""Tests des Job-Runners (Ausführung, Fehlerisolation, Ergebnis)."""

from __future__ import annotations

from datetime import UTC, datetime

from models.operations import JobStatus, ScheduledJob
from operations.job_runner import run_job
from tests.operations_helpers import make_discovery_report

_JOB = ScheduledJob(name="europe_open", job_type="discovery", time="09:00", timezone="UTC")
_NOW = datetime(2024, 6, 3, 7, 0, tzinfo=UTC)


def test_success_run():
    run, result = run_job(_JOB, lambda: "ok", _NOW, now_fn=lambda: _NOW)
    assert run.status is JobStatus.SUCCESS
    assert run.error == ""
    assert result == "ok"


def test_failed_run_isolated():
    def boom():
        raise RuntimeError("kaputt")

    run, result = run_job(_JOB, boom, _NOW, now_fn=lambda: _NOW)
    assert run.status is JobStatus.FAILED
    assert "kaputt" in run.error
    assert result is None


def test_run_records_times():
    run, _ = run_job(_JOB, lambda: "ok", _NOW, now_fn=lambda: _NOW)
    assert run.started_at == _NOW
    assert run.finished_at == _NOW
    assert run.scheduled_at == _NOW


def test_run_measures_duration():
    counter = iter([1.0, 1.5])
    run, _ = run_job(_JOB, lambda: "ok", _NOW, now_fn=lambda: _NOW, timer=lambda: next(counter))
    assert run.duration_seconds == 0.5


def test_summary_for_discovery_report():
    report = make_discovery_report(("AAPL", "NVDA"))
    run, _ = run_job(_JOB, lambda: report, _NOW, now_fn=lambda: _NOW)
    assert "2 Opportunities" in run.summary


def test_summary_for_string():
    run, _ = run_job(_JOB, lambda: "done", _NOW, now_fn=lambda: _NOW)
    assert run.summary == "done"


def test_summary_for_none():
    run, _ = run_job(_JOB, lambda: None, _NOW, now_fn=lambda: _NOW)
    assert run.summary == ""


def test_failed_run_has_no_summary():
    def boom():
        raise ValueError("x")

    run, _ = run_job(_JOB, boom, _NOW, now_fn=lambda: _NOW)
    assert run.summary == ""


def test_run_carries_job_identity():
    run, _ = run_job(_JOB, lambda: "ok", _NOW, now_fn=lambda: _NOW)
    assert run.name == "europe_open"
    assert run.job_type == "discovery"


def test_does_not_raise_on_arbitrary_exception():
    def boom():
        raise KeyError("missing")

    run, result = run_job(_JOB, boom, _NOW, now_fn=lambda: _NOW)
    assert run.status is JobStatus.FAILED
    assert result is None
