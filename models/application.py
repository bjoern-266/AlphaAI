"""Datentypen der Application- und API-Schicht (unveränderlich).

Diese Modelle beschreiben ausschließlich, **wie** bestehende Reports über die
REST-API bereitgestellt werden. Sie enthalten **keine** Handels-, Analyse- oder
Berechnungslogik: keine Scores, keine Risiken, keine Empfehlungen. Die
eigentlichen Fach-Reports (Operations, Discovery, Opportunities, …) bleiben
unverändert und werden von der Application-Schicht nur gelesen, versioniert
gespeichert und als JSON ausgeliefert.

Alle Typen sind ``frozen`` und ``slots`` – sie können daher gefahrlos per
Dependency Injection weitergereicht und zwischengespeichert werden.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class HealthStatus(Enum):
    """Gesundheitszustand einer Komponente oder des Gesamtsystems.

    Die Reihenfolge (aufsteigende Schwere) erlaubt eine einfache Aggregation:
    der schlechteste Komponentenzustand bestimmt den Gesamtzustand.
    """

    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"
    UNKNOWN = "unknown"


class ReportKind(Enum):
    """Bekannte Report-Arten, die über die API bereitgestellt werden.

    Der Wert ist zugleich der stabile Speicher-Schlüssel (Persistenz) und der
    ``kind`` in den API-Metadaten. Neue Arten werden hier ergänzt; bestehende
    Werte bleiben aus Kompatibilitätsgründen unverändert.
    """

    OPERATIONS = "operations"
    DISCOVERY = "discovery"
    OPPORTUNITIES = "opportunities"
    RECOMMENDATIONS = "recommendations"
    ANALYTICS = "analytics"
    BACKTESTING = "backtesting"
    PAPER_TRADING = "paper_trading"
    DASHBOARD = "dashboard"


@dataclass(frozen=True, slots=True)
class ApiVersion:
    """Versionskennung der REST-API.

    Attributes:
        api: Semantische API-Version (z. B. ``"v1"``) – Teil des URL-Präfixes.
        service: Version des Backend-Dienstes.
        released: Anzeigename/Datum der Freigabe (frei, dient der Dokumentation).
    """

    api: str = "v1"
    service: str = "1.0.0"
    released: str = ""


@dataclass(frozen=True, slots=True)
class ServiceInfo:
    """Statische Beschreibung des laufenden Backend-Dienstes.

    Attributes:
        name: Anzeigename des Dienstes.
        version: Version des Backend-Dienstes.
        api_version: Aktive API-Version (z. B. ``"v1"``).
        environment: Betriebsumgebung (z. B. ``"local"``/``"production"``).
        description: Kurzbeschreibung (frei).
        started_at: Startzeitpunkt des Dienstes (UTC) oder ``None``.
        uptime_seconds: Laufzeit in Sekunden oder ``None``.
    """

    name: str = "AlphaAI Backend"
    version: str = "1.0.0"
    api_version: str = "v1"
    environment: str = "local"
    description: str = ""
    started_at: datetime | None = None
    uptime_seconds: int | None = None


@dataclass(frozen=True, slots=True)
class ComponentHealth:
    """Gesundheitszustand einer einzelnen Komponente.

    Attributes:
        name: Name der Komponente (z. B. ``"scheduler"``, ``"cache"``).
        status: Zustand der Komponente.
        detail: Menschenlesbare Erläuterung des Zustands.
        metrics: Zusätzliche Kennzahlen (nur Ablesewerte, keine Berechnung).
    """

    name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    detail: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HealthReport:
    """Aggregierter Gesundheitszustand des Backend-Dienstes.

    Attributes:
        status: Gesamtzustand (schlechtester Komponentenzustand).
        components: Zustände der einzelnen Komponenten.
        as_of: Bezugszeitpunkt (UTC) oder ``None``.
        uptime_seconds: Laufzeit des Dienstes in Sekunden oder ``None``.
        version: Version des Backend-Dienstes.
    """

    status: HealthStatus = HealthStatus.UNKNOWN
    components: tuple[ComponentHealth, ...] = ()
    as_of: datetime | None = None
    uptime_seconds: int | None = None
    version: str = ""

    @property
    def healthy(self) -> bool:
        """``True``, wenn der Gesamtzustand ``OK`` ist."""
        return self.status is HealthStatus.OK

    def component(self, name: str) -> ComponentHealth | None:
        """Gibt den Zustand einer benannten Komponente zurück (oder ``None``)."""
        for item in self.components:
            if item.name == name:
                return item
        return None


@dataclass(frozen=True, slots=True)
class StoredReport:
    """Ein dauerhaft gespeicherter Report-Schnappschuss.

    Attributes:
        kind: Report-Art (Wert aus :class:`ReportKind`).
        created_at: Erzeugungszeitpunkt (UTC).
        sequence: Fortlaufende Nummer der Speicherung (aufsteigend).
        payload: Der bereits JSON-fähig serialisierte Report.
        report_version: Fachliche Versionsnummer des Reports (aus Metadaten).
    """

    kind: str
    created_at: datetime
    payload: dict[str, Any]
    sequence: int = 0
    report_version: int = 0


@dataclass(frozen=True, slots=True)
class ApiError:
    """Strukturierte Fehlerinformation einer API-Antwort.

    Attributes:
        status: HTTP-Statuscode (z. B. 400, 404, 503).
        code: Stabiler, maschinenlesbarer Fehlercode (z. B. ``"not_found"``).
        message: Menschenlesbare Fehlermeldung.
        detail: Optionale Zusatzinformationen (z. B. ungültiger Parameter).
    """

    status: int
    code: str
    message: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ApiEnvelope:
    """Einheitliche Hülle jeder API-Antwort.

    Jede Antwort – ob Erfolg oder Fehler – hat dieselbe äußere Form. Das
    erleichtert die spätere Android-Anbindung (Sprint 18) und hält die API
    stabil und versionierbar.

    Attributes:
        ok: ``True`` bei Erfolg, ``False`` bei Fehler.
        data: Die Nutzdaten (bereits JSON-fähig) oder ``None`` bei Fehlern.
        error: Fehlerinformation oder ``None`` bei Erfolg.
        meta: Metadaten (API-Version, ``kind``, Zeitstempel, Cache-Hinweis, …).
    """

    ok: bool
    data: Any = None
    error: ApiError | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EndpointInfo:
    """Beschreibung eines registrierten API-Endpunkts (für ``/`` und Doku).

    Attributes:
        method: HTTP-Methode (aktuell ausschließlich ``"GET"``).
        path: Pfad-Vorlage relativ zum API-Präfix (z. B. ``"/opportunities/{ticker}"``).
        name: Stabiler Name des Endpunkts.
        description: Kurzbeschreibung.
        report_kind: Zugrunde liegende Report-Art (oder leer für System-Endpunkte).
    """

    method: str
    path: str
    name: str
    description: str = ""
    report_kind: str = ""


__all__ = [
    "HealthStatus",
    "ReportKind",
    "ApiVersion",
    "ServiceInfo",
    "ComponentHealth",
    "HealthReport",
    "StoredReport",
    "ApiError",
    "ApiEnvelope",
    "EndpointInfo",
]
