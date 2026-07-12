"""Application Engine – Composition Root des produktiven Backend-Dienstes.

Die :class:`ApplicationEngine` verdrahtet die gesamte Application-Schicht zu
einem lauffähigen Backend-Dienst: den dauerhaften Report-Speicher, die
Lesedienste, das Health-Monitoring, die REST-API (framework-unabhängig) und –
optional – den Hintergrunddienst, der den (injizierten) Operations-Taktgeber
antreibt und die Reports persistiert.

Sie ist die **einzige** Stelle, die sowohl die ``application``-Schicht als auch
die Pipeline-nahen Engines kennt. Dadurch bleibt ``application`` frei von
Engine-Importen (keine Import-Zyklen), und die eigentliche Analyse-Pipeline wird
ausschließlich **injiziert**. Die Engine führt selbst **keine** Analyse aus und
trifft **keine** Handelsentscheidung.

Alle Betriebsparameter stammen aus ``knowledge/application_rules.toml`` – es gibt
keine hartcodierten Werte.
"""

from __future__ import annotations

import tomllib
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from application.api import ApplicationApi
from application.api.router import ApiRequest, ApiResponse
from application.api.routes import build_router
from application.authentication import AuthPolicy, LocalOnlyPolicy, OpenPolicy
from application.health import HealthMonitor
from application.repositories import ReportStore
from application.services import BackgroundService, ReportService, SystemService
from application.services.background_service import TickResult
from core.cache import Cache
from core.exceptions import AlphaAIError
from core.paths import DATABASE_DIR, KNOWLEDGE_DIR
from engines.application_registry import ApplicationRegistry, build_default_registry
from models.application import HealthReport, ServiceInfo

APPLICATION_RULES_FILE = KNOWLEDGE_DIR / "application_rules.toml"

_AUTH_POLICIES: dict[str, Callable[[], AuthPolicy]] = {
    "local_only": LocalOnlyPolicy,
    "open": OpenPolicy,
}


class ApplicationRulesError(AlphaAIError):
    """Wird ausgelöst, wenn die Application-Regeln fehlen oder ungültig sind."""


class ApplicationRules:
    """Geladene Betriebsparameter des Backend-Dienstes.

    Attributes:
        service: Statische Dienstbeschreibung.
        database_file: Dateiname/-pfad der SQLite-Datenbank.
        retention: Maximale Anzahl gespeicherter Reports je Art (0 = unbegrenzt).
        cache_capacity: Kapazität des Antwort-Caches.
        default_top_limit: Standardanzahl der Top-Chancen.
        auth_policy: Name der Zugriffsrichtlinie ("local_only"/"open").
        version: Versionsnummer der Regeldatei.
    """

    def __init__(
        self,
        service: ServiceInfo,
        database_file: str,
        retention: int,
        cache_capacity: int,
        default_top_limit: int,
        auth_policy: str,
        version: int,
    ) -> None:
        self.service = service
        self.database_file = database_file
        self.retention = retention
        self.cache_capacity = cache_capacity
        self.default_top_limit = default_top_limit
        self.auth_policy = auth_policy
        self.version = version


def load_application_rules(path: Path | None = None) -> ApplicationRules:
    """Lädt die Application-Regeln aus der TOML-Datei.

    Raises:
        ApplicationRulesError: Wenn die Datei fehlt oder ungültig ist.
    """
    rules_path = path or APPLICATION_RULES_FILE
    if not rules_path.is_file():
        raise ApplicationRulesError(f"Regeldatei nicht gefunden: {rules_path}")
    try:
        with rules_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise ApplicationRulesError(f"Regeln sind kein gültiges TOML: {error}") from error
    return load_application_rules_from_dict(data)


def load_application_rules_from_dict(data: Mapping[str, Any]) -> ApplicationRules:
    """Baut :class:`ApplicationRules` aus einer geparsten TOML-Struktur.

    Raises:
        ApplicationRulesError: Wenn Pflichtwerte fehlen oder ungültig sind.
    """
    service = data.get("service", {})
    persistence = data.get("persistence", {})
    api = data.get("api", {})
    meta = data.get("meta", {})

    database_file = str(persistence.get("database_file", "alpha_ai_reports.db"))
    if not database_file:
        raise ApplicationRulesError("persistence.database_file darf nicht leer sein.")

    auth_policy = str(api.get("auth_policy", "local_only"))
    if auth_policy not in _AUTH_POLICIES:
        raise ApplicationRulesError(
            f"Unbekannte api.auth_policy '{auth_policy}'. Erlaubt: {sorted(_AUTH_POLICIES)}."
        )

    retention = int(persistence.get("retention", 200))
    cache_capacity = int(api.get("cache_capacity", 256))
    default_top_limit = int(api.get("default_top_limit", 10))
    if retention < 0:
        raise ApplicationRulesError("persistence.retention darf nicht negativ sein.")
    if cache_capacity < 1:
        raise ApplicationRulesError("api.cache_capacity muss mindestens 1 sein.")
    if default_top_limit < 1:
        raise ApplicationRulesError("api.default_top_limit muss mindestens 1 sein.")

    api_version = str(service.get("api_version", "v1"))
    info = ServiceInfo(
        name=str(service.get("name", "AlphaAI Backend")),
        version=str(service.get("version", "1.0.0")),
        api_version=api_version,
        environment=str(service.get("environment", "local")),
        description=str(service.get("description", "")),
    )
    return ApplicationRules(
        service=info,
        database_file=database_file,
        retention=retention,
        cache_capacity=cache_capacity,
        default_top_limit=default_top_limit,
        auth_policy=auth_policy,
        version=int(meta.get("version", 0)),
    )


class ApplicationEngine:
    """Verdrahtet und betreibt den produktiven Backend-Dienst.

    Args:
        rules: Geladene Betriebsparameter.
        store: Dauerhafter Report-Speicher. Standard: SQLite-Datei laut Regeln.
        operations: Optionaler, injizierter Operations-Taktgeber. Nur wenn
            vorhanden, kann der Hintergrunddienst Takte ausführen.
        report_sources: Optionale, injizierte Fach-Report-Quellen (Art → Funktion).
        registry: Registry der bekannten Report-Arten (Standard: alle Standardarten).
        clock: Zeitquelle (UTC, injizierbar für Tests).
    """

    def __init__(
        self,
        rules: ApplicationRules,
        *,
        store: ReportStore | None = None,
        operations: Any = None,
        report_sources: Mapping[str, Callable[[], Any]] | None = None,
        registry: ApplicationRegistry | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._rules = rules
        self._clock = clock
        self._registry = registry or build_default_registry()
        self._store = store or ReportStore(
            _database_path(rules.database_file), retention=rules.retention
        )
        self._reports = ReportService(self._store)
        self._system = SystemService(self._store, rules.service, started_at=clock(), clock=clock)
        self._api: ApplicationApi | None = None
        # Der Cache-Bezug wird verzögert aufgelöst (die Fassade existiert gleich):
        # zur Aufrufzeit von ``report()`` ist ``self._api`` bereits gesetzt.
        self._health = HealthMonitor(
            self._store,
            version=rules.service.version,
            cache_metrics=self._cache_metrics,
            clock=clock,
        )
        router = build_router(
            self._reports,
            self._system,
            self._health,
            api_version=rules.service.api_version,
        )
        cache: Cache[ApiResponse] = Cache(capacity=rules.cache_capacity)
        self._api = ApplicationApi(
            router,
            self._store,
            auth_policy=_AUTH_POLICIES[rules.auth_policy](),
            cache=cache,
            api_version=rules.service.api_version,
        )
        self._background: BackgroundService | None = None
        if operations is not None:
            self._background = BackgroundService(
                operations,
                self._store,
                report_sources=report_sources,
                clock=clock,
            )

    @classmethod
    def from_config(
        cls,
        path: Path | None = None,
        *,
        store: ReportStore | None = None,
        operations: Any = None,
        report_sources: Mapping[str, Callable[[], Any]] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> ApplicationEngine:
        """Erzeugt eine Engine mit Regeln aus der Konfigurationsdatei."""
        kwargs: dict[str, Any] = {
            "rules": load_application_rules(path),
            "store": store,
            "operations": operations,
            "report_sources": report_sources,
        }
        if clock is not None:
            kwargs["clock"] = clock
        return cls(**kwargs)

    # ------------------------------------------------------------------ #
    # Zugriff
    # ------------------------------------------------------------------ #
    @property
    def api(self) -> ApplicationApi:
        """Die framework-unabhängige API-Fassade."""
        return self._api

    @property
    def store(self) -> ReportStore:
        """Der dauerhafte Report-Speicher."""
        return self._store

    @property
    def registry(self) -> ApplicationRegistry:
        """Die Registry der bekannten Report-Arten."""
        return self._registry

    @property
    def reports(self) -> ReportService:
        """Der Lesedienst für gespeicherte Reports."""
        return self._reports

    @property
    def background(self) -> BackgroundService | None:
        """Der Hintergrunddienst (oder ``None``, falls kein Taktgeber injiziert)."""
        return self._background

    # ------------------------------------------------------------------ #
    # Betrieb
    # ------------------------------------------------------------------ #
    def start(self, now: datetime | None = None) -> TickResult:
        """Startet den Hintergrunddienst (erster Takt inkl. Persistenz).

        Raises:
            ApplicationRulesError: Wenn kein Operations-Taktgeber injiziert wurde.
        """
        if self._background is None:
            raise ApplicationRulesError(
                "Kein Operations-Taktgeber injiziert – start() nicht möglich."
            )
        return self._background.start(now)

    def tick(self, now: datetime | None = None) -> TickResult:
        """Führt einen Hintergrund-Takt aus (Scheduler/Heartbeat/Persistenz).

        Raises:
            ApplicationRulesError: Wenn kein Operations-Taktgeber injiziert wurde.
        """
        if self._background is None:
            raise ApplicationRulesError(
                "Kein Operations-Taktgeber injiziert – tick() nicht möglich."
            )
        return self._background.tick(now)

    def handle(self, request: ApiRequest) -> ApiResponse:
        """Beantwortet eine API-Anfrage über die Fassade."""
        return self._api.handle(request)

    def health(self) -> HealthReport:
        """Gibt den aktuellen aggregierten Health-Report zurück."""
        return self._health.report()

    def create_fastapi_app(self, api_prefix: str = "/api/v1") -> Any:
        """Baut die FastAPI-App für den produktiven Betrieb (optionaler Adapter)."""
        from application.api.service import create_fastapi_app

        return create_fastapi_app(self._api, api_prefix=api_prefix)

    # ------------------------------------------------------------------ #
    # Interner Aufbau
    # ------------------------------------------------------------------ #
    def _cache_metrics(self) -> dict[str, int]:
        """Liefert die Cache-Kennzahlen der Fassade (verzögert, für den Health-Monitor)."""
        return self._api.cache_metrics() if self._api is not None else {}


def _database_path(database_file: str) -> str:
    """Bestimmt den Datenbankpfad (absolut oder relativ zu ``database/``)."""
    candidate = Path(database_file)
    if candidate.is_absolute() or database_file == ":memory:":
        return database_file
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    return str(DATABASE_DIR / candidate)


__all__ = [
    "ApplicationEngine",
    "ApplicationRules",
    "ApplicationRulesError",
    "APPLICATION_RULES_FILE",
    "load_application_rules",
    "load_application_rules_from_dict",
]
