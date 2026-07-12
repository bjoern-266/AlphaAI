"""Job-Runner: führt einen (injizierten) Job aus und protokolliert den Lauf.

Der Runner ruft die **injizierte** Job-Funktion auf, misst die Laufzeit und fängt
Fehler ab, sodass ein Absturz eines Jobs den Scheduler **niemals** blockiert. Er
enthält **keine** Fachlogik – die eigentliche Analyse liegt in der bestehenden
Pipeline (per Injektion).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from core.logging_config import get_logger
from models.market_discovery import DiscoveryReport
from models.operations import JobRun, JobStatus, ScheduledJob

_logger = get_logger(__name__)

# Signatur einer injizierten Job-Funktion (liefert ein beliebiges Ergebnis).
JobFunc = Callable[[], Any]


def _summarize(result: Any) -> str:
    """Erzeugt eine kurze Ergebnis-Beschreibung (nur Anzeige)."""
    if isinstance(result, DiscoveryReport):
        rejected = result.statistics.rejected_count
        return f"{result.opportunity_count} Opportunities, {rejected} verworfen"
    if result is None:
        return ""
    return str(result)


def run_job(
    job: ScheduledJob,
    func: JobFunc,
    scheduled_at: datetime | None,
    now_fn: Callable[[], datetime] = lambda: datetime.now(UTC),
    timer: Callable[[], float] = time.perf_counter,
) -> tuple[JobRun, Any]:
    """Führt einen Job aus und liefert den Lauf-Report plus Ergebnis.

    Fehler werden isoliert (Status ``FAILED``); es wird **keine** Exception nach
    außen geworfen.
    """
    started = now_fn()
    start_counter = timer()
    result: Any = None
    status = JobStatus.SUCCESS
    error = ""
    try:
        result = func()
    except Exception as exception:  # Ein Job-Absturz darf den Scheduler nie blockieren.
        _logger.warning("Job '%s' fehlgeschlagen: %s", job.name, exception)
        status = JobStatus.FAILED
        error = str(exception)
    finished = now_fn()
    duration = timer() - start_counter
    run = JobRun(
        name=job.name,
        job_type=job.job_type,
        status=status,
        scheduled_at=scheduled_at,
        started_at=started,
        finished_at=finished,
        duration_seconds=duration,
        error=error,
        summary=_summarize(result) if status is JobStatus.SUCCESS else "",
    )
    return run, result
