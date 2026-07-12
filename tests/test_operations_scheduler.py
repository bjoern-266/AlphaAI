"""Tests des Schedulers (fällige/nächste Jobs, Zeitzonen)."""

from __future__ import annotations

from datetime import UTC, datetime

from operations.scheduler import due_jobs, load_schedule, next_scan, scheduled_at

_SCHEDULE = load_schedule(
    [
        {
            "name": "europe_open",
            "job_type": "discovery",
            "time": "09:00",
            "timezone": "Europe/Berlin",
        },
        {
            "name": "us_open",
            "job_type": "discovery",
            "time": "09:30",
            "timezone": "America/New_York",
        },
        {
            "name": "disabled",
            "job_type": "analytics",
            "time": "10:00",
            "timezone": "UTC",
            "enabled": False,
        },
    ]
)


def test_load_schedule_fields():
    assert _SCHEDULE[0].name == "europe_open"
    assert _SCHEDULE[0].job_type == "discovery"
    assert _SCHEDULE[2].enabled is False


def test_scheduled_at_utc():
    now = datetime(2024, 6, 3, 12, 0, tzinfo=UTC)
    planned = scheduled_at(_SCHEDULE[0], now)  # 09:00 Berlin = 07:00 UTC
    assert planned == datetime(2024, 6, 3, 7, 0, tzinfo=UTC)


def test_scheduled_at_day_offset():
    now = datetime(2024, 6, 3, 12, 0, tzinfo=UTC)
    planned = scheduled_at(_SCHEDULE[0], now, day_offset=1)
    assert planned.date() == datetime(2024, 6, 4, tzinfo=UTC).date()


def test_due_jobs_after_time():
    now = datetime(
        2024, 6, 3, 12, 0, tzinfo=UTC
    )  # nach 07:00 UTC und 13:30 UTC? us=13:30 noch nicht
    due = due_jobs(_SCHEDULE, now, {})
    names = {job.name for job in due}
    assert "europe_open" in names
    assert "us_open" not in names  # 09:30 NY = 13:30 UTC, noch nicht erreicht


def test_due_jobs_ignores_disabled():
    now = datetime(2024, 6, 3, 20, 0, tzinfo=UTC)
    due = due_jobs(_SCHEDULE, now, {})
    assert all(job.name != "disabled" for job in due)


def test_due_jobs_not_repeated_same_day():
    now = datetime(2024, 6, 3, 12, 0, tzinfo=UTC)
    planned = scheduled_at(_SCHEDULE[0], now)
    last_run = {"europe_open": planned}  # bereits gelaufen
    due = due_jobs(_SCHEDULE, now, last_run)
    assert all(job.name != "europe_open" for job in due)


def test_due_jobs_repeats_next_day():
    day1 = datetime(2024, 6, 3, 12, 0, tzinfo=UTC)
    last_run = {"europe_open": scheduled_at(_SCHEDULE[0], day1)}
    day2 = datetime(2024, 6, 4, 12, 0, tzinfo=UTC)
    due = due_jobs(_SCHEDULE, day2, last_run)
    assert any(job.name == "europe_open" for job in due)


def test_due_jobs_before_time_empty():
    now = datetime(2024, 6, 3, 5, 0, tzinfo=UTC)  # vor 07:00 UTC
    due = due_jobs(_SCHEDULE, now, {})
    assert all(job.name != "europe_open" for job in due)


def test_next_scan_returns_upcoming():
    now = datetime(2024, 6, 3, 8, 0, tzinfo=UTC)  # nach europe_open, vor us_open
    job, at = next_scan(_SCHEDULE, now)
    assert job.name == "us_open"  # 13:30 UTC als nächstes
    assert at == datetime(2024, 6, 3, 13, 30, tzinfo=UTC)


def test_next_scan_wraps_to_next_day():
    now = datetime(2024, 6, 3, 20, 0, tzinfo=UTC)  # alle heute vorbei
    job, at = next_scan(_SCHEDULE, now)
    assert at.date() == datetime(2024, 6, 4, tzinfo=UTC).date()
    assert job.name == "europe_open"  # frühester am Folgetag


def test_next_scan_ignores_disabled():
    _, at = next_scan(_SCHEDULE, datetime(2024, 6, 3, 8, 0, tzinfo=UTC))
    assert at is not None


def test_next_scan_empty_schedule():
    job, at = next_scan([], datetime(2024, 6, 3, tzinfo=UTC))
    assert job is None
    assert at is None


def test_due_jobs_empty_schedule():
    assert due_jobs([], datetime(2024, 6, 3, tzinfo=UTC), {}) == ()


def test_winter_scheduled_at_shifts():
    now = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)
    planned = scheduled_at(_SCHEDULE[0], now)  # 09:00 Berlin CET = 08:00 UTC im Winter
    assert planned == datetime(2024, 1, 15, 8, 0, tzinfo=UTC)
