"""Hintergrunddienst: Takt geben und Reports dauerhaft speichern.

Der :class:`BackgroundService` betreibt das Backend im laufenden Betrieb. Bei
jedem Takt lässt er den (injizierten) Operations-Taktgeber laufen – dieser
startet Scheduler, Heartbeat, Marktuhr und fällige Analyse-Jobs – und speichert
anschließend die entstandenen Reports dauerhaft. Zusätzliche Fach-Reports
(Empfehlungen, Chancen, Analytics …) werden über **injizierte** Report-Quellen
bezogen; die eigentliche Analyse-Pipeline bleibt unverändert und wird nicht
importiert.

Robustheit (Recovery): Ein Fehler in einem einzelnen Takt oder einer einzelnen
Report-Quelle darf den Dienst **niemals** dauerhaft anhalten. Jeder Schritt ist
gekapselt; Fehler werden gezählt und protokolliert, der Takt läuft weiter.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from application.repositories import ReportStore
from application.serialization import to_jsonable
from core.logging_config import get_logger
from models.application import ReportKind

_logger = get_logger(__name__)


class _OperationsTicker(Protocol):
    """Duck-Typing-Vertrag des injizierten Operations-Taktgebers."""

    def beat(self, now: datetime | None = ...) -> None:
        """Setzt den Heartbeat."""
        ...

    def tick(self, now: datetime | None = ...) -> Any:
        """Führt einen Takt aus und liefert den Operations-Report."""
        ...


@dataclass(frozen=True, slots=True)
class TickResult:
    """Ergebnis eines Takts (nur Ablesewerte, keine Fachlogik).

    Attributes:
        as_of: Zeitpunkt des Takts (UTC).
        stored_kinds: Report-Arten, die in diesem Takt gespeichert wurden.
        errors: Aufgetretene Fehler (Quelle -> Meldung); leer bei Erfolg.
    """

    as_of: datetime
    stored_kinds: tuple[str, ...] = ()
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """``True``, wenn im Takt kein Fehler auftrat."""
        return not self.errors


class BackgroundService:
    """Betreibt den Backend-Takt und persistiert die Reports.

    Args:
        operations: Injizierter Operations-Taktgeber (Scheduler/Heartbeat/Markt).
        store: Der dauerhafte Report-Speicher.
        report_sources: Zuordnung Report-Art → **injizierte** Funktion, die den
            jeweiligen Fach-Report liefert (oder ``None`` überspringt die Art).
        clock: Zeitquelle (UTC, injizierbar für Tests).
    """

    def __init__(
        self,
        operations: _OperationsTicker,
        store: ReportStore,
        *,
        report_sources: Mapping[str, Callable[[], Any]] | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._operations = operations
        self._store = store
        self._sources = dict(report_sources or {})
        self._clock = clock
        self._started = False
        self._tick_count = 0
        self._error_count = 0

    @property
    def started(self) -> bool:
        """``True``, sobald der Dienst gestartet wurde."""
        return self._started

    @property
    def tick_count(self) -> int:
        """Anzahl bisher ausgeführter Takte."""
        return self._tick_count

    @property
    def error_count(self) -> int:
        """Anzahl bisher aufgetretener (aufgefangener) Fehler."""
        return self._error_count

    def start(self, now: datetime | None = None) -> TickResult:
        """Startet den Dienst: Heartbeat setzen und ersten Takt ausführen.

        Ein Fehler beim Start hält den Dienst nicht auf – er wird gezählt und der
        Dienst gilt dennoch als gestartet (Recovery).
        """
        moment = now or self._clock()
        self._started = True
        try:
            self._operations.beat(moment)
        except Exception as error:  # noqa: BLE001 - Start darf nie hart fehlschlagen
            self._error_count += 1
            _logger.warning("Heartbeat beim Start fehlgeschlagen: %s", error)
        return self.tick(moment)

    def tick(self, now: datetime | None = None) -> TickResult:
        """Führt einen Takt aus und speichert alle entstandenen Reports.

        Der Takt läuft immer bis zum Ende; einzelne Fehler werden aufgefangen,
        gezählt und im Ergebnis vermerkt. Der Dienst bleibt stets betriebsbereit.
        """
        moment = now or self._clock()
        self._tick_count += 1
        stored: list[str] = []
        errors: dict[str, str] = {}

        self._run_operations(moment, stored, errors)
        for kind, source in self._sources.items():
            self._run_source(kind, source, stored, errors)

        self._error_count += len(errors)
        return TickResult(as_of=moment, stored_kinds=tuple(stored), errors=errors)

    def run_cycles(self, count: int, start_at: datetime | None = None) -> tuple[TickResult, ...]:
        """Führt ``count`` Takte nacheinander aus (für Betrieb/Tests).

        Der erste Takt startet den Dienst, falls er noch nicht gestartet wurde.
        """
        results: list[TickResult] = []
        for index in range(max(int(count), 0)):
            moment = start_at if (start_at is not None and index == 0) else None
            results.append(self.start(moment) if not self._started else self.tick(moment))
        return tuple(results)

    # ------------------------------------------------------------------ #
    # Interne Schritte (jeweils gekapselt – Recovery)
    # ------------------------------------------------------------------ #
    def _run_operations(self, now: datetime, stored: list[str], errors: dict[str, str]) -> None:
        """Führt den Operations-Takt aus und speichert dessen Report."""
        try:
            report = self._operations.tick(now)
            self._persist(ReportKind.OPERATIONS.value, report, now)
            stored.append(ReportKind.OPERATIONS.value)
        except Exception as error:  # noqa: BLE001 - Takt darf nie hart fehlschlagen
            errors[ReportKind.OPERATIONS.value] = str(error)
            _logger.error("Operations-Takt fehlgeschlagen: %s", error)

    def _run_source(
        self,
        kind: str,
        source: Callable[[], Any],
        stored: list[str],
        errors: dict[str, str],
    ) -> None:
        """Bezieht einen Fach-Report aus einer Quelle und speichert ihn."""
        try:
            report = source()
            if report is None:
                return
            self._persist(kind, report, self._clock())
            stored.append(kind)
        except Exception as error:  # noqa: BLE001 - Quelle darf den Takt nie stoppen
            errors[kind] = str(error)
            _logger.error("Report-Quelle '%s' fehlgeschlagen: %s", kind, error)

    def _persist(self, kind: str, report: Any, now: datetime) -> None:
        """Serialisiert einen Report und speichert ihn dauerhaft."""
        payload = to_jsonable(report)
        if not isinstance(payload, dict):
            payload = {"value": payload}
        self._store.save(
            kind,
            payload,
            created_at=now,
            report_version=_report_version(report),
        )


def _report_version(report: Any) -> int:
    """Liest die fachliche Versionsnummer aus den Report-Metadaten (oder 0)."""
    metadata = getattr(report, "metadata", None)
    if isinstance(metadata, Mapping):
        for key in ("rules_version", "version"):
            value = metadata.get(key)
            if isinstance(value, int):
                return value
    return 0


__all__ = ["BackgroundService", "TickResult"]
