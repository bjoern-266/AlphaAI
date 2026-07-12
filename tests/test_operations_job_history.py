"""Tests der Job-Historie (Ringpuffer, Kennzahlen)."""

from __future__ import annotations

from models.operations import JobRun, JobStatus
from operations.job_history import JobHistory


def _run(name: str, status: JobStatus = JobStatus.SUCCESS, duration: float | None = 1.0) -> JobRun:
    return JobRun(name=name, job_type="discovery", status=status, duration_seconds=duration)


def test_add_newest_first():
    history = JobHistory()
    history.add(_run("a"))
    history.add(_run("b"))
    assert [run.name for run in history.all()] == ["b", "a"]


def test_recent_limit():
    history = JobHistory()
    for i in range(5):
        history.add(_run(f"j{i}"))
    assert len(history.recent(2)) == 2


def test_len():
    history = JobHistory()
    history.add(_run("a"))
    assert len(history) == 1


def test_ringbuffer_limit():
    history = JobHistory(limit=3)
    for i in range(5):
        history.add(_run(f"j{i}"))
    assert len(history) == 3
    # Neueste bleiben erhalten.
    assert history.all()[0].name == "j4"


def test_success_count():
    history = JobHistory()
    history.add(_run("a", JobStatus.SUCCESS))
    history.add(_run("b", JobStatus.FAILED))
    history.add(_run("c", JobStatus.SUCCESS))
    assert history.success_count == 2


def test_error_count():
    history = JobHistory()
    history.add(_run("a", JobStatus.FAILED))
    history.add(_run("b", JobStatus.SUCCESS))
    assert history.error_count == 1


def test_average_runtime():
    history = JobHistory()
    history.add(_run("a", duration=1.0))
    history.add(_run("b", duration=3.0))
    assert history.average_runtime() == 2.0


def test_average_runtime_empty():
    assert JobHistory().average_runtime() is None


def test_average_runtime_ignores_none():
    history = JobHistory()
    history.add(_run("a", duration=None))
    history.add(_run("b", duration=2.0))
    assert history.average_runtime() == 2.0


def test_recent_zero():
    history = JobHistory()
    history.add(_run("a"))
    assert history.recent(0) == ()


def test_limit_minimum_one():
    history = JobHistory(limit=0)
    history.add(_run("a"))
    assert len(history) == 1
