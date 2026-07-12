"""Scheduler: bestimmt fällige und nächste Analyse-Jobs.

Wertet die geplanten Jobs (Uhrzeiten aus der Konfiguration) gegen einen Zeitpunkt
und die letzten Laufzeiten aus. Ein Job ist **fällig**, wenn seine heutige geplante
Zeit erreicht/überschritten ist und er seither noch nicht lief. Es findet **keine**
Fachlogik statt – nur Zeitplanung. Sommer-/Winterzeit über die IANA-Zeitzone.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from models.operations import ScheduledJob
from operations.market_sessions import parse_time


def load_schedule(entries: Sequence[Mapping[str, Any]]) -> tuple[ScheduledJob, ...]:
    """Baut die geplanten Jobs aus der ``[[schedule]]``-Konfiguration."""
    jobs: list[ScheduledJob] = []
    for entry in entries:
        parse_time(entry["time"])  # validiert das Format früh
        jobs.append(
            ScheduledJob(
                name=str(entry["name"]),
                job_type=str(entry["job_type"]),
                time=str(entry["time"]),
                timezone=str(entry.get("timezone", "UTC")),
                enabled=bool(entry.get("enabled", True)),
                description=str(entry.get("description", "")),
            )
        )
    return tuple(jobs)


def scheduled_at(job: ScheduledJob, now: datetime, day_offset: int = 0) -> datetime:
    """Geplanter Zeitpunkt eines Jobs am (lokalen) Tag von ``now`` (+ Offset), UTC."""
    tz = ZoneInfo(job.timezone)
    local = now.astimezone(tz)
    midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
    start = midnight + timedelta(days=day_offset, minutes=parse_time(job.time))
    return start.astimezone(UTC)


def due_jobs(
    schedule: Sequence[ScheduledJob],
    now: datetime,
    last_run: Mapping[str, datetime],
) -> tuple[ScheduledJob, ...]:
    """Gibt die aktuell fälligen Jobs zurück (geplante Zeit erreicht, noch nicht gelaufen)."""
    due: list[ScheduledJob] = []
    for job in schedule:
        if not job.enabled:
            continue
        planned = scheduled_at(job, now)
        if now >= planned:
            last = last_run.get(job.name)
            if last is None or last < planned:
                due.append(job)
    return tuple(due)


def next_scan(
    schedule: Sequence[ScheduledJob], now: datetime
) -> tuple[ScheduledJob | None, datetime | None]:
    """Gibt den nächsten geplanten Job und seinen Zeitpunkt zurück."""
    best_job: ScheduledJob | None = None
    best_at: datetime | None = None
    for job in schedule:
        if not job.enabled:
            continue
        planned = scheduled_at(job, now)
        if planned <= now:
            planned = scheduled_at(job, now, day_offset=1)
        if best_at is None or planned < best_at:
            best_at = planned
            best_job = job
    return best_job, best_at
