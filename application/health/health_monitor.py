"""Aggregiert den Gesundheitszustand aller Backend-Komponenten.

Der :class:`HealthMonitor` bildet aus bereits vorhandenen Zustandswerten einen
Gesamt-Health-Report. Er **liest** dazu den zuletzt gespeicherten
Operations-Report (für Scheduler/Markt/Queue/System) sowie Kennzahlen des
Speichers und – optional – des Antwort-Caches. Der Gesamtzustand ist der
schlechteste Komponentenzustand (OK < DEGRADED < ERROR).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any

from application.repositories import ReportStore
from models.application import ComponentHealth, HealthReport, HealthStatus, ReportKind

# Rangordnung zur Aggregation (höher = schlechter).
_SEVERITY = {
    HealthStatus.OK: 0,
    HealthStatus.UNKNOWN: 1,
    HealthStatus.DEGRADED: 2,
    HealthStatus.ERROR: 3,
}
# Zuordnung des Operations-Health-Textes auf den API-Health-Status.
_OPERATIONS_HEALTH = {
    "ok": HealthStatus.OK,
    "degraded": HealthStatus.DEGRADED,
    "error": HealthStatus.ERROR,
}


class HealthMonitor:
    """Erzeugt aggregierte Health-Reports aus vorhandenen Zustandswerten.

    Args:
        store: Der dauerhafte Report-Speicher (liest u. a. den Operations-Report).
        version: Version des Backend-Dienstes (nur Anzeige).
        cache_metrics: Optionale Quelle für Cache-Kennzahlen (``hits``/``misses``/
            ``size``/``capacity``). Wird keine übergeben, gilt der Cache als
            unbekannt.
        clock: Zeitquelle (UTC, injizierbar für Tests).
    """

    def __init__(
        self,
        store: ReportStore,
        *,
        version: str = "",
        cache_metrics: Callable[[], Mapping[str, Any]] | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._store = store
        self._version = version
        self._cache_metrics = cache_metrics
        self._clock = clock

    def report(self) -> HealthReport:
        """Baut den aggregierten :class:`HealthReport`."""
        operations = self._latest_operations()
        components = (
            self._api_health(),
            self._persistence_health(),
            self._scheduler_health(operations),
            self._market_health(operations),
            self._queue_health(operations),
            self._cache_health(),
            self._system_health(operations),
        )
        overall = self._aggregate(components)
        uptime = _dig(operations, "system_state", "uptime_seconds")
        return HealthReport(
            status=overall,
            components=components,
            as_of=self._clock(),
            uptime_seconds=uptime if isinstance(uptime, int) else None,
            version=self._version,
        )

    # ------------------------------------------------------------------ #
    # Einzelkomponenten
    # ------------------------------------------------------------------ #
    def _api_health(self) -> ComponentHealth:
        """Die API antwortet – daher ist sie im Moment der Prüfung erreichbar."""
        return ComponentHealth(name="api", status=HealthStatus.OK, detail="API erreichbar.")

    def _persistence_health(self) -> ComponentHealth:
        """Bewertet die Persistenz anhand der Erreichbarkeit und des Bestands."""
        try:
            total = self._store.count()
        except Exception as error:  # noqa: BLE001 - Zustand darf nie hart fehlschlagen
            return ComponentHealth(name="persistence", status=HealthStatus.ERROR, detail=str(error))
        status = HealthStatus.OK if total > 0 else HealthStatus.DEGRADED
        detail = "Reports gespeichert." if total > 0 else "Noch keine Reports gespeichert."
        return ComponentHealth(
            name="persistence", status=status, detail=detail, metrics={"stored_reports": total}
        )

    def _scheduler_health(self, operations: Mapping[str, Any] | None) -> ComponentHealth:
        """Bewertet den Scheduler anhand von Heartbeat und System-Health."""
        if operations is None:
            return ComponentHealth(
                name="scheduler",
                status=HealthStatus.UNKNOWN,
                detail="Noch kein Operations-Report vorhanden.",
            )
        alive = _dig(operations, "system_state", "heartbeat", "alive")
        next_job = operations.get("next_scan_job") or ""
        status = HealthStatus.OK if alive else HealthStatus.DEGRADED
        detail = "Heartbeat aktiv." if alive else "Kein aktueller Heartbeat."
        return ComponentHealth(
            name="scheduler",
            status=status,
            detail=detail,
            metrics={
                "next_scan_job": next_job,
                "next_scan_at": operations.get("next_scan_at"),
                "running_job": operations.get("running_job"),
            },
        )

    def _market_health(self, operations: Mapping[str, Any] | None) -> ComponentHealth:
        """Bewertet die Marktuhr anhand vorhandener Marktzustände."""
        if operations is None:
            return ComponentHealth(
                name="market", status=HealthStatus.UNKNOWN, detail="Keine Marktuhr vorhanden."
            )
        clock = operations.get("market_clock") or {}
        markets = clock.get("markets") or []
        open_markets = clock.get("open_markets") or []
        status = HealthStatus.OK if markets else HealthStatus.DEGRADED
        return ComponentHealth(
            name="market",
            status=status,
            detail=f"{len(open_markets)} von {len(markets)} Märkten geöffnet.",
            metrics={"markets": len(markets), "open_markets": len(open_markets)},
        )

    def _queue_health(self, operations: Mapping[str, Any] | None) -> ComponentHealth:
        """Bewertet die Job-Queue anhand ihrer Größe."""
        if operations is None:
            return ComponentHealth(
                name="queue", status=HealthStatus.UNKNOWN, detail="Keine Queue-Information."
            )
        size = _dig(operations, "system_state", "queue_size")
        size = size if isinstance(size, int) else 0
        return ComponentHealth(
            name="queue",
            status=HealthStatus.OK,
            detail=f"{size} Job(s) in der Warteschlange.",
            metrics={"queue_size": size, "running_job": operations.get("running_job")},
        )

    def _cache_health(self) -> ComponentHealth:
        """Bewertet den Antwort-Cache anhand seiner Kennzahlen (falls vorhanden)."""
        if self._cache_metrics is None:
            return ComponentHealth(
                name="cache", status=HealthStatus.UNKNOWN, detail="Kein Cache angeschlossen."
            )
        try:
            metrics = dict(self._cache_metrics())
        except Exception as error:  # noqa: BLE001 - Zustand darf nie hart fehlschlagen
            return ComponentHealth(name="cache", status=HealthStatus.ERROR, detail=str(error))
        return ComponentHealth(
            name="cache",
            status=HealthStatus.OK,
            detail="Cache aktiv.",
            metrics=metrics,
        )

    def _system_health(self, operations: Mapping[str, Any] | None) -> ComponentHealth:
        """Bewertet das Gesamtsystem anhand des System-Health-Feldes."""
        if operations is None:
            return ComponentHealth(
                name="system", status=HealthStatus.UNKNOWN, detail="Kein System-Zustand."
            )
        raw = str(_dig(operations, "system_state", "health") or "unknown").lower()
        status = _OPERATIONS_HEALTH.get(raw, HealthStatus.UNKNOWN)
        errors = _dig(operations, "system_state", "error_count")
        return ComponentHealth(
            name="system",
            status=status,
            detail=f"System-Zustand: {raw}.",
            metrics={
                "error_count": errors if isinstance(errors, int) else 0,
                "scan_count": _dig(operations, "system_state", "scan_count"),
                "uptime_seconds": _dig(operations, "system_state", "uptime_seconds"),
            },
        )

    # ------------------------------------------------------------------ #
    # Hilfen
    # ------------------------------------------------------------------ #
    def _latest_operations(self) -> Mapping[str, Any] | None:
        """Liest den zuletzt gespeicherten Operations-Report (oder ``None``)."""
        stored = self._store.latest(ReportKind.OPERATIONS.value)
        return stored.payload if stored is not None else None

    @staticmethod
    def _aggregate(components: tuple[ComponentHealth, ...]) -> HealthStatus:
        """Bestimmt den schlechtesten Komponentenzustand als Gesamtzustand."""
        worst = HealthStatus.OK
        for component in components:
            if _SEVERITY[component.status] > _SEVERITY[worst]:
                worst = component.status
        return worst


def _dig(source: Mapping[str, Any] | None, *keys: str) -> Any:
    """Liest verschachtelte Werte aus einem Dict-Baum (``None`` bei Fehlstelle)."""
    current: Any = source
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


__all__ = ["HealthMonitor"]
