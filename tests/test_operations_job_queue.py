"""Tests der Job-Queue (Serialisierung, Exklusivität, Duplikatschutz)."""

from __future__ import annotations

from models.operations import ScheduledJob
from operations.job_queue import JobQueue


def _job(name: str, job_type: str = "discovery") -> ScheduledJob:
    return ScheduledJob(name=name, job_type=job_type, time="09:00", timezone="UTC")


def test_submit_and_size():
    queue = JobQueue()
    assert queue.submit(_job("a", "analytics"))
    assert queue.size == 1


def test_duplicate_name_rejected():
    queue = JobQueue()
    queue.submit(_job("a", "analytics"))
    assert queue.submit(_job("a", "analytics")) is False
    assert queue.size == 1


def test_only_one_discovery_pending():
    queue = JobQueue()
    assert queue.submit(_job("d1", "discovery"))
    assert queue.submit(_job("d2", "discovery")) is False
    assert queue.size == 1


def test_non_exclusive_types_allowed():
    queue = JobQueue()
    assert queue.submit(_job("a", "analytics"))
    assert queue.submit(_job("b", "analytics"))
    assert queue.size == 2


def test_start_next_runs_one():
    queue = JobQueue()
    queue.submit(_job("a", "analytics"))
    queue.submit(_job("b", "analytics"))
    first = queue.start_next()
    assert first.name == "a"
    assert queue.running.name == "a"
    # Nur einer gleichzeitig: solange einer läuft, startet kein weiterer.
    assert queue.start_next() is None


def test_complete_frees_slot():
    queue = JobQueue()
    queue.submit(_job("a", "analytics"))
    queue.submit(_job("b", "analytics"))
    queue.start_next()
    queue.complete()
    assert queue.running is None
    assert queue.start_next().name == "b"


def test_discovery_blocked_while_running():
    queue = JobQueue()
    queue.submit(_job("d1", "discovery"))
    queue.start_next()
    # Während ein Discovery läuft, wird kein weiteres angenommen.
    assert queue.submit(_job("d2", "discovery")) is False


def test_discovery_allowed_after_complete():
    queue = JobQueue()
    queue.submit(_job("d1", "discovery"))
    queue.start_next()
    queue.complete()
    assert queue.submit(_job("d2", "discovery"))


def test_start_next_empty():
    assert JobQueue().start_next() is None


def test_clear():
    queue = JobQueue()
    queue.submit(_job("a", "analytics"))
    queue.start_next()
    queue.clear()
    assert queue.size == 0
    assert queue.running is None


def test_custom_exclusive_types():
    queue = JobQueue(exclusive_types=("analytics",))
    assert queue.submit(_job("a", "analytics"))
    assert queue.submit(_job("b", "analytics")) is False
    assert queue.submit(_job("d", "discovery"))  # discovery hier nicht exklusiv


def test_running_none_initially():
    assert JobQueue().running is None


def test_fifo_order():
    queue = JobQueue()
    for name in ("a", "b", "c"):
        queue.submit(_job(name, "analytics"))
    order = []
    while True:
        job = queue.start_next()
        if job is None:
            break
        order.append(job.name)
        queue.complete()
    assert order == ["a", "b", "c"]


def test_duplicate_running_name_rejected():
    queue = JobQueue()
    queue.submit(_job("a", "analytics"))
    queue.start_next()
    assert queue.submit(_job("a", "analytics")) is False
