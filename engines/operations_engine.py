"""Operations Engine – der automatische Taktgeber der Live Operations Platform.

Die :class:`OperationsEngine` erkennt automatisch die Marktzeiten, plant die
Analyse-Jobs, führt fällige Jobs (über **injizierte** Job-Funktionen) sicher aus
und stellt jederzeit einen :class:`~models.operations.OperationReport` bereit. Sie
führt **niemals** Orders aus, trifft **keine** Handelsentscheidung und
**berechnet keine** Indikatoren/Muster/Strategien/Scores/Risiken/Empfehlungen.

Parameter stammen ausschließlich aus ``knowledge/operations_rules.toml``. Neue
Job-Arten werden nur über die ``OperationsRegistry`` ergänzt – die Engine bleibt
**unverändert** (Open/Closed). Die eigentliche Analyse (Market Discovery etc.)
wird **injiziert**; die Engine importiert dafür nichts aus der Pipeline.
"""

from __future__ import annotations

import time
import tomllib
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.exceptions import AlphaAIError
from core.paths import KNOWLEDGE_DIR
from engines.operations_registry import OperationsRegistry, build_default_registry
from models.market_discovery import DiscoveryReport
from models.operations import (
    JobRun,
    JobStatus,
    MarketClock,
    OperationReport,
    ScheduledJob,
    SystemState,
)
from operations.heartbeat import build_heartbeat
from operations.job_history import JobHistory
from operations.job_queue import JobQueue
from operations.job_runner import JobFunc, run_job
from operations.market_clock import build_market_clock
from operations.market_sessions import MarketSession, load_sessions
from operations.scheduler import due_jobs, load_schedule, next_scan, scheduled_at
from operations.system_state import build_system_state

OPERATIONS_RULES_FILE = KNOWLEDGE_DIR / "operations_rules.toml"

_RECENT_HISTORY = 20


class OperationsRulesError(AlphaAIError):
    """Wird ausgelöst, wenn die Operations-Regeln fehlen oder ungültig sind."""


class OperationsRules:
    """Geladene Operations-Regeln.

    Attributes:
        sessions: Marktsitzungen (Phasen je Markt).
        schedule: Geplante Jobs.
        heartbeat_interval: Erwartetes Heartbeat-Intervall (Sekunden).
        degraded_ratio: Fehleranteil, ab dem der Zustand „degraded" ist.
        history_limit: Maximale Anzahl gespeicherter Job-Läufe.
        version: Versionsnummer der Regeldatei.
    """

    def __init__(
        self,
        sessions: tuple[MarketSession, ...],
        schedule: tuple[ScheduledJob, ...],
        heartbeat_interval: int,
        degraded_ratio: float,
        history_limit: int,
        version: int,
    ) -> None:
        self.sessions = sessions
        self.schedule = schedule
        self.heartbeat_interval = heartbeat_interval
        self.degraded_ratio = degraded_ratio
        self.history_limit = history_limit
        self.version = version


def load_operations_rules(path: Path | None = None) -> OperationsRules:
    """Lädt die Operations-Regeln aus der TOML-Datei.

    Raises:
        OperationsRulesError: Wenn die Datei fehlt oder ungültig ist.
    """
    rules_path = path or OPERATIONS_RULES_FILE
    if not rules_path.is_file():
        raise OperationsRulesError(f"Regeldatei nicht gefunden: {rules_path}")
    try:
        with rules_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise OperationsRulesError(f"Regeln sind kein gültiges TOML: {error}") from error
    return load_operations_rules_from_dict(data)


def load_operations_rules_from_dict(data: Mapping[str, Any]) -> OperationsRules:
    """Baut :class:`OperationsRules` aus einer geparsten TOML-Struktur.

    Raises:
        OperationsRulesError: Wenn Märkte/Zeitplan/Zeiten/Zeitzonen ungültig sind.
    """
    from operations.market_sessions import MarketSessionError

    markets = data.get("markets", {})
    if not isinstance(markets, Mapping) or not markets:
        raise OperationsRulesError("Abschnitt [markets] fehlt oder ist leer.")
    try:
        sessions = load_sessions(markets)
    except MarketSessionError as error:
        raise OperationsRulesError(str(error)) from error

    schedule_raw = data.get("schedule", [])
    if not isinstance(schedule_raw, Sequence) or isinstance(schedule_raw, (str, bytes)):
        raise OperationsRulesError("Abschnitt [[schedule]] muss eine Liste sein.")
    try:
        schedule = load_schedule(schedule_raw)
    except (MarketSessionError, KeyError) as error:
        raise OperationsRulesError(f"Ungültiger Zeitplan: {error}") from error
    names = [job.name for job in schedule]
    if len(names) != len(set(names)):
        raise OperationsRulesError("Doppelte Job-Namen im Zeitplan.")

    heartbeat = data.get("heartbeat", {})
    health = data.get("health", {})
    history = data.get("history", {})
    meta = data.get("meta", {})
    return OperationsRules(
        sessions=sessions,
        schedule=schedule,
        heartbeat_interval=int(heartbeat.get("interval_seconds", 60)),
        degraded_ratio=float(health.get("degraded_ratio", 0.3)),
        history_limit=int(history.get("limit", 100)),
        version=int(meta.get("version", 0)),
    )


class OperationsEngine:
    """Automatischer Taktgeber: plant Jobs und baut den OperationReport.

    Args:
        rules: Geladene Regeln.
        registry: Registry der bekannten Job-Arten (Standard: alle Standardarten).
        jobs: Zuordnung Job-Art → **injizierte** Funktion (die eigentliche Analyse).
        clock: Zeitquelle (UTC, injizierbar für Tests).
        timer: Laufzeitquelle (injizierbar für Tests).
    """

    def __init__(
        self,
        rules: OperationsRules,
        registry: OperationsRegistry | None = None,
        jobs: Mapping[str, JobFunc] | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._rules = rules
        self._registry = registry or build_default_registry()
        self._jobs = dict(jobs or {})
        self._clock = clock
        self._timer = timer
        self._queue = JobQueue(
            exclusive_types=tuple(
                name for name in self._registry.names() if self._registry.get(name).exclusive
            )
        )
        self._history = JobHistory(limit=rules.history_limit)
        self._last_run: dict[str, datetime] = {}
        self._scan_count = 0
        self._error_count = 0
        self._last_error = ""
        self._last_successful_scan_at: datetime | None = None
        self._last_beat_at: datetime | None = None
        self._started_at: datetime | None = None
        self._latest_discovery: DiscoveryReport | None = None
        self._previous_tickers: set[str] = set()
        self._new_opportunities: tuple[str, ...] = ()
        self._new_risks: tuple[str, ...] = ()

    @classmethod
    def from_config(
        cls,
        path: Path | None = None,
        jobs: Mapping[str, JobFunc] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> OperationsEngine:
        """Erzeugt eine Engine mit Regeln aus der Konfigurationsdatei."""
        kwargs: dict[str, Any] = {"rules": load_operations_rules(path), "jobs": jobs}
        if clock is not None:
            kwargs["clock"] = clock
        return cls(**kwargs)

    @property
    def registry(self) -> OperationsRegistry:
        """Die Registry der bekannten Job-Arten."""
        return self._registry

    def beat(self, now: datetime | None = None) -> None:
        """Setzt den Heartbeat (und initialisiert die Uptime beim ersten Aufruf)."""
        moment = now or self._clock()
        self._last_beat_at = moment
        if self._started_at is None:
            self._started_at = moment

    def tick(self, now: datetime | None = None) -> OperationReport:
        """Führt einen Takt aus: Heartbeat, fällige Jobs starten, Report bauen."""
        moment = now or self._clock()
        self.beat(moment)
        for job in due_jobs(self._rules.schedule, moment, self._last_run):
            if job.job_type not in self._registry:
                self._record_skip(job, moment, f"Unbekannte Job-Art '{job.job_type}'.")
                continue
            self._queue.submit(job)
        self._drain_queue(moment)
        return self.build_report(moment)

    def _drain_queue(self, now: datetime) -> None:
        """Arbeitet die Queue seriell ab (nur ein Job gleichzeitig)."""
        while True:
            job = self._queue.start_next()
            if job is None:
                break
            self._run(job, now)
            self._queue.complete()

    def _run(self, job: ScheduledJob, now: datetime) -> None:
        """Führt einen Job aus, protokolliert ihn und aktualisiert die Zähler."""
        self._last_run[job.name] = now
        func = self._jobs.get(job.job_type)
        if func is None:
            self._record_skip(job, now, "Keine Job-Funktion registriert.")
            return
        run, result = run_job(
            job, func, scheduled_at(job, now), now_fn=lambda: now, timer=self._timer
        )
        self._history.add(run)
        if run.status is JobStatus.FAILED:
            self._error_count += 1
            self._last_error = run.error
            return
        self._scan_count += 1
        self._last_successful_scan_at = run.finished_at
        if isinstance(result, DiscoveryReport):
            self._update_discovery(result)

    def _record_skip(self, job: ScheduledJob, now: datetime, reason: str) -> None:
        """Protokolliert einen übersprungenen Job (fehlende Registrierung/Funktion)."""
        self._last_run[job.name] = now
        self._history.add(
            JobRun(
                name=job.name,
                job_type=job.job_type,
                status=JobStatus.SKIPPED,
                scheduled_at=scheduled_at(job, now),
                summary=reason,
            )
        )

    def _update_discovery(self, report: DiscoveryReport) -> None:
        """Übernimmt den letzten Discovery-Report und bestimmt Neuzugänge."""
        current = {opportunity.ticker for opportunity in report.opportunities}
        self._new_opportunities = tuple(sorted(current - self._previous_tickers))
        self._new_risks = tuple(
            sorted(
                opportunity.ticker
                for opportunity in report.opportunities
                if opportunity.warnings and opportunity.ticker not in self._previous_tickers
            )
        )
        self._previous_tickers = current
        self._latest_discovery = report

    def build_report(self, now: datetime | None = None) -> OperationReport:
        """Baut den aktuellen :class:`OperationReport` (reine Zusammenstellung)."""
        moment = now or self._clock()
        clock = build_market_clock(self._rules.sessions, moment)
        heartbeat = build_heartbeat(self._last_beat_at, moment, self._rules.heartbeat_interval)
        running = self._queue.running.name if self._queue.running is not None else None
        uptime = (
            int((moment - self._started_at).total_seconds())
            if self._started_at is not None
            else None
        )
        system_state = build_system_state(
            heartbeat=heartbeat,
            running_job=running,
            queue_size=self._queue.size,
            scan_count=self._scan_count,
            error_count=self._error_count,
            last_error=self._last_error,
            uptime_seconds=uptime,
            degraded_ratio=self._rules.degraded_ratio,
        )
        next_job, next_at = next_scan(self._rules.schedule, moment)
        return OperationReport(
            as_of=moment,
            market_clock=clock,
            current_session=_describe_session(clock),
            last_successful_scan_at=self._last_successful_scan_at,
            next_scan_at=next_at,
            next_scan_job=next_job.name if next_job is not None else "",
            running_job=running,
            job_history=self._history.recent(_RECENT_HISTORY),
            system_state=system_state,
            scan_count=self._scan_count,
            error_count=self._error_count,
            average_runtime=self._history.average_runtime(),
            discovery=self._latest_discovery,
            new_opportunities=self._new_opportunities,
            new_risks=self._new_risks,
            metadata={"rules_version": self._rules.version},
        )


def _describe_session(clock: MarketClock) -> str:
    """Beschreibt die laufende Börsensitzung (Anzeige-Text)."""
    open_markets = [market for market in clock.markets if market.is_open]
    if not open_markets:
        return "Alle Märkte geschlossen"
    return " · ".join(f"{market.title}: {market.phase}" for market in open_markets)


__all__ = [
    "OperationsEngine",
    "OperationsRules",
    "OperationsRulesError",
    "OPERATIONS_RULES_FILE",
    "load_operations_rules",
    "load_operations_rules_from_dict",
    "SystemState",
]
