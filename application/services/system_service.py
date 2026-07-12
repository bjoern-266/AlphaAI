"""Systemdienst: Version und Statuszusammenfassung des Backends.

Der :class:`SystemService` liefert statische Dienstinformationen (Name,
Version, API-Version, Umgebung) sowie eine kompakte Statuszusammenfassung
(Uptime, gespeicherte Reports, letzter Scan). Er **liest** ausschließlich – er
berechnet keine Fachdaten.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from application.repositories import ReportStore
from application.serialization import to_jsonable
from models.application import ReportKind, ServiceInfo


class SystemService:
    """Liefert Version und Statuszusammenfassung des Backend-Dienstes.

    Args:
        store: Der dauerhafte Report-Speicher (für Zähler/letzter Scan).
        info: Statische Dienstbeschreibung (Name/Version/API-Version/Umgebung).
        started_at: Startzeitpunkt des Dienstes (UTC). Standard: jetzt.
        clock: Zeitquelle (UTC, injizierbar für Tests).
    """

    def __init__(
        self,
        store: ReportStore,
        info: ServiceInfo | None = None,
        *,
        started_at: datetime | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._store = store
        self._clock = clock
        self._started_at = started_at or clock()
        self._info = info or ServiceInfo()

    def _uptime_seconds(self) -> int:
        """Berechnet die Laufzeit in ganzen Sekunden seit dem Start."""
        return max(int((self._clock() - self._started_at).total_seconds()), 0)

    def service_info(self) -> ServiceInfo:
        """Gibt die aktuelle Dienstbeschreibung inkl. Uptime zurück."""
        from dataclasses import replace

        return replace(
            self._info,
            started_at=self._started_at,
            uptime_seconds=self._uptime_seconds(),
        )

    def version(self) -> dict[str, Any]:
        """Gibt Version und Dienstbeschreibung als JSON-fähiges Dict zurück."""
        return to_jsonable(self.service_info())

    def status(self) -> dict[str, Any]:
        """Gibt eine kompakte Statuszusammenfassung des Dienstes zurück.

        Enthält Dienstbeschreibung, Uptime, Anzahl gespeicherter Reports je Art
        sowie den zuletzt gespeicherten Operations-Systemzustand (falls vorhanden).
        """
        operations = self._store.latest(ReportKind.OPERATIONS.value)
        system_state = operations.payload.get("system_state") if operations is not None else None
        stored_counts = {kind.value: self._store.count(kind.value) for kind in ReportKind}
        return {
            "service": to_jsonable(self.service_info()),
            "uptime_seconds": self._uptime_seconds(),
            "stored_reports": stored_counts,
            "last_scan_at": (
                operations.payload.get("last_successful_scan_at")
                if operations is not None
                else None
            ),
            "system_state": system_state,
        }


__all__ = ["SystemService"]
