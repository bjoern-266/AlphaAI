"""Domänenmodell: Live Market Operations.

Enthält die unveränderlichen Datentypen der Live Market Operations Platform. Die
Plattform macht AlphaAI zu einem **produktiven täglichen Analyse-System**: sie
erkennt automatisch die Marktzeiten, plant die Analyse-Jobs (Market Discovery,
Scanner, Analytics, …) und stellt jederzeit einen belastbaren Systemzustand
bereit. Sie führt **niemals** Orders aus und trifft **keine**
Handelsentscheidung; sie **berechnet keine** Indikatoren/Muster/Strategien/
Scores/Risiken/Empfehlungen, sondern **orchestriert** die bestehende Pipeline.

Alle Reports sind **UI-unabhängig** (Desktop-Dashboard, spätere REST-API und
mobile Apps nutzen dieselben Reports – keine doppelte Geschäftslogik).

Teil der Entities-Schicht (``models/``). Abhängigkeiten zeigen nur auf andere
Modelle (:mod:`models.market_discovery`) bzw. die Standardbibliothek – **kein**
Import aus ``engines``, ``operations`` o. Ä.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from models.market_discovery import DiscoveryReport


class JobStatus(Enum):
    """Status eines Analyse-Jobs."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class SystemHealth(Enum):
    """Gesamtzustand des Systems."""

    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class MarketState:
    """Zustand eines Marktes zu einem Zeitpunkt (unveränderlich).

    Attributes:
        key: Markt-Schlüssel (z. B. ``"europe"``/``"us"``).
        title: Anzeigename.
        timezone: Zeitzone des Marktes (IANA, z. B. ``"Europe/Berlin"``).
        phase: Name der aktuellen Marktphase.
        is_open: Ob der Markt aktuell geöffnet ist.
        next_phase: Name der nächsten Marktphase.
        next_change_at: Zeitpunkt des nächsten Phasenwechsels (UTC).
        seconds_to_next: Countdown bis zum nächsten Phasenwechsel (Sekunden).
    """

    key: str
    title: str
    timezone: str
    phase: str
    is_open: bool
    next_phase: str
    next_change_at: datetime | None
    seconds_to_next: int | None


@dataclass(frozen=True, slots=True)
class MarketClock:
    """Marktuhr: der Zustand aller Märkte zu einem Zeitpunkt (unveränderlich).

    Attributes:
        as_of: Bezugszeitpunkt (UTC).
        markets: Zustand aller Märkte.
        next_open_market: Schlüssel des als nächstes öffnenden Marktes.
        next_open_at: Zeitpunkt der nächsten Marktöffnung (UTC).
    """

    as_of: datetime
    markets: tuple[MarketState, ...] = ()
    next_open_market: str = ""
    next_open_at: datetime | None = None

    @property
    def open_markets(self) -> tuple[str, ...]:
        """Schlüssel der aktuell geöffneten Märkte."""
        return tuple(market.key for market in self.markets if market.is_open)

    @property
    def closed_markets(self) -> tuple[str, ...]:
        """Schlüssel der aktuell geschlossenen Märkte."""
        return tuple(market.key for market in self.markets if not market.is_open)

    def get(self, key: str) -> MarketState | None:
        """Gibt den Zustand eines Marktes zurück (oder ``None``)."""
        for market in self.markets:
            if market.key == key:
                return market
        return None


@dataclass(frozen=True, slots=True)
class JobRun:
    """Ein einzelner Job-Lauf (unveränderlich).

    Attributes:
        name: Eindeutiger Job-Name.
        job_type: Job-Art (z. B. ``"discovery"``/``"analytics"``).
        status: Status des Laufs.
        scheduled_at: Geplanter Startzeitpunkt (UTC).
        started_at: Tatsächlicher Start (UTC) oder ``None``.
        finished_at: Ende (UTC) oder ``None``.
        duration_seconds: Laufzeit in Sekunden (oder ``None``).
        error: Fehlermeldung (leer, wenn erfolgreich).
        summary: Menschenlesbare Ergebnis-Kurzfassung.
        metadata: Zusatzinformationen.
    """

    name: str
    job_type: str
    status: JobStatus
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_seconds: float | None = None
    error: str = ""
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """Ob der Lauf erfolgreich war."""
        return self.status is JobStatus.SUCCESS


@dataclass(frozen=True, slots=True)
class ScheduledJob:
    """Ein geplanter Job (Definition, unveränderlich).

    Attributes:
        name: Eindeutiger Name (z. B. ``"europe_open"``).
        job_type: Job-Art (muss in der Registry bekannt sein).
        time: Uhrzeit ``HH:MM`` (in der Zeitzone ``timezone``).
        timezone: Zeitzone der Uhrzeit (IANA).
        enabled: Ob der Job aktiv ist.
        description: Beschreibung (Anzeige).
    """

    name: str
    job_type: str
    time: str
    timezone: str
    enabled: bool = True
    description: str = ""


@dataclass(frozen=True, slots=True)
class JobDefinition:
    """Definition einer bekannten Job-Art (Registry-Eintrag, unveränderlich).

    Attributes:
        name: Job-Art-Schlüssel (z. B. ``"discovery"``) – zugleich Registry-Name.
        title: Anzeigename.
        description: Beschreibung.
        exclusive: Ob höchstens einer dieser Jobs gleichzeitig laufen darf.
    """

    name: str
    title: str = ""
    description: str = ""
    exclusive: bool = False


@dataclass(frozen=True, slots=True)
class Heartbeat:
    """Heartbeat des Systems (unveränderlich).

    Attributes:
        alive: Ob das System als „lebendig" gilt.
        last_beat_at: Zeitpunkt des letzten Herzschlags (UTC).
        age_seconds: Alter des letzten Herzschlags in Sekunden.
        interval_seconds: Erwartetes Herzschlag-Intervall.
    """

    alive: bool
    last_beat_at: datetime | None = None
    age_seconds: int | None = None
    interval_seconds: int = 60


@dataclass(frozen=True, slots=True)
class SystemState:
    """Gesamtzustand des Systems (unveränderlich).

    Attributes:
        health: Gesundheitszustand.
        heartbeat: Aktueller Heartbeat.
        running_job: Name des laufenden Jobs (oder ``None``).
        queue_size: Anzahl wartender Jobs.
        scan_count: Anzahl bisher gelaufener Scans.
        error_count: Anzahl bisher aufgetretener Fehler.
        last_error: Letzte Fehlermeldung.
        uptime_seconds: Laufzeit des Systems in Sekunden.
    """

    health: SystemHealth = SystemHealth.OK
    heartbeat: Heartbeat | None = None
    running_job: str | None = None
    queue_size: int = 0
    scan_count: int = 0
    error_count: int = 0
    last_error: str = ""
    uptime_seconds: int | None = None


@dataclass(frozen=True, slots=True)
class OperationReport:
    """Gesamt-Report der Live Operations Platform (unveränderlich, UI-unabhängig).

    Dieser Report ist die **einzige** Schnittstelle für Anzeigen (Dashboard,
    spätere REST-API, mobile Apps). Er enthält keine Geschäfts-/Handelslogik.

    Attributes:
        as_of: Bezugszeitpunkt (UTC).
        market_clock: Zustand aller Märkte.
        current_session: Beschreibung der laufenden Börsensitzung.
        last_successful_scan_at: Zeitpunkt des letzten erfolgreichen Scans.
        next_scan_at: Zeitpunkt des nächsten geplanten Scans.
        next_scan_job: Name des nächsten geplanten Scans.
        running_job: Name des laufenden Jobs (oder ``None``).
        job_history: Verlauf der letzten Job-Läufe (neueste zuerst).
        system_state: Systemzustand (Health/Heartbeat/…).
        scan_count: Anzahl gelaufener Scans.
        error_count: Anzahl aufgetretener Fehler.
        average_runtime: Durchschnittliche Job-Laufzeit (Sekunden) oder ``None``.
        discovery: Der letzte Discovery-Report (Top Opportunities) oder ``None``.
        new_opportunities: Seit dem letzten Scan neu aufgetauchte Ticker.
        new_risks: Seit dem letzten Scan neu mit Warnungen versehene Ticker.
        valid: Ob der Report grundsätzlich verwertbar ist.
        warnings: Gesammelte Warnungen.
        metadata: Zusatzinformationen.
    """

    as_of: datetime
    market_clock: MarketClock
    current_session: str = ""
    last_successful_scan_at: datetime | None = None
    next_scan_at: datetime | None = None
    next_scan_job: str = ""
    running_job: str | None = None
    job_history: tuple[JobRun, ...] = ()
    system_state: SystemState = field(default_factory=SystemState)
    scan_count: int = 0
    error_count: int = 0
    average_runtime: float | None = None
    discovery: DiscoveryReport | None = None
    new_opportunities: tuple[str, ...] = ()
    new_risks: tuple[str, ...] = ()
    valid: bool = True
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def open_markets(self) -> tuple[str, ...]:
        """Schlüssel der aktuell geöffneten Märkte."""
        return self.market_clock.open_markets

    def recent_jobs(self, limit: int) -> tuple[JobRun, ...]:
        """Gibt die letzten ``limit`` Job-Läufe zurück."""
        return self.job_history[: max(limit, 0)]


__all__ = [
    "JobStatus",
    "SystemHealth",
    "MarketState",
    "MarketClock",
    "JobRun",
    "ScheduledJob",
    "JobDefinition",
    "Heartbeat",
    "SystemState",
    "OperationReport",
]
