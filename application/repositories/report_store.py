"""SQLite-gestützter Report-Speicher (dauerhaft, neustartfest).

Der :class:`ReportStore` speichert jeden Report-Schnappschuss als JSON-Nutzlast
in einer SQLite-Datenbank. SQLite ist eine eingebettete, transaktionale
Produktionsdatenbank – die Daten liegen dauerhaft auf der Platte, überstehen
Neustarts und benötigen keinen separaten Serverprozess.

Speichermodell (eine Tabelle ``reports``):

* ``kind`` – Report-Art (Speicher-Schlüssel),
* ``sequence`` – fortlaufende Nummer (Autoincrement, global),
* ``created_at`` – Erzeugungszeitpunkt (ISO-8601, UTC),
* ``report_version`` – fachliche Versionsnummer aus den Report-Metadaten,
* ``payload`` – der bereits serialisierte Report als JSON-Text.

Der jeweils **neueste** Eintrag je ``kind`` ist der „letzte erfolgreiche Scan".
Ältere Einträge bleiben als Historie erhalten (begrenzbar via ``retention``).

Der Store ist über einen Lock threadsicher – der Hintergrunddienst schreibt,
die API liest nebenläufig.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from application.exceptions import PersistenceError
from models.application import StoredReport

_SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    sequence       INTEGER PRIMARY KEY AUTOINCREMENT,
    kind           TEXT    NOT NULL,
    created_at     TEXT    NOT NULL,
    report_version INTEGER NOT NULL DEFAULT 0,
    payload        TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reports_kind_seq ON reports (kind, sequence DESC);
"""


class ReportStore:
    """Dauerhafter, threadsicherer Speicher für Report-Schnappschüsse.

    Args:
        path: Pfad zur SQLite-Datei. ``":memory:"`` ist ausschließlich für Tests
            vorgesehen; im produktiven Betrieb wird stets eine Datei verwendet.
        retention: Maximale Anzahl gespeicherter Einträge **je** ``kind``. Ältere
            Einträge werden beim Speichern verworfen. ``0`` = unbegrenzt.
    """

    def __init__(self, path: str | Path = ":memory:", retention: int = 200) -> None:
        self._path = str(path)
        self._retention = max(retention, 0)
        self._lock = threading.RLock()
        # ``check_same_thread=False``: der Zugriff wird über den Lock serialisiert.
        try:
            self._connection = sqlite3.connect(self._path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            with self._connection:
                self._connection.executescript(_SCHEMA)
            row = self._connection.execute("SELECT MAX(sequence) AS m FROM reports").fetchone()
            self._revision = int(row["m"] or 0)
        except sqlite3.Error as error:  # pragma: no cover - Infrastrukturfehler
            raise PersistenceError(f"Report-Speicher nicht initialisierbar: {error}") from error

    # ------------------------------------------------------------------ #
    # Schreiben
    # ------------------------------------------------------------------ #
    def save(
        self,
        kind: str,
        payload: dict[str, Any],
        *,
        created_at: datetime | None = None,
        report_version: int = 0,
    ) -> StoredReport:
        """Speichert einen Report-Schnappschuss dauerhaft.

        Args:
            kind: Report-Art (Speicher-Schlüssel).
            payload: Der bereits JSON-fähig serialisierte Report.
            created_at: Erzeugungszeitpunkt (UTC); Standard ist „jetzt".
            report_version: Fachliche Versionsnummer aus den Report-Metadaten.

        Returns:
            Der gespeicherte :class:`StoredReport` inkl. vergebener ``sequence``.

        Raises:
            PersistenceError: Wenn das Schreiben fehlschlägt.
        """
        moment = created_at or datetime.now(UTC)
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        with self._lock:
            try:
                cursor = self._connection.execute(
                    "INSERT INTO reports (kind, created_at, report_version, payload) "
                    "VALUES (?, ?, ?, ?)",
                    (kind, moment.isoformat(), int(report_version), text),
                )
                sequence = int(cursor.lastrowid or 0)
                self._revision = max(self._revision, sequence)
                self._enforce_retention(kind)
                self._connection.commit()
            except sqlite3.Error as error:
                raise PersistenceError(
                    f"Report konnte nicht gespeichert werden: {error}"
                ) from error
        return StoredReport(
            kind=kind,
            created_at=moment,
            payload=payload,
            sequence=sequence,
            report_version=int(report_version),
        )

    def _enforce_retention(self, kind: str) -> None:
        """Verwirft älteste Einträge einer Art, sobald ``retention`` überschritten ist."""
        if self._retention == 0:
            return
        self._connection.execute(
            "DELETE FROM reports WHERE kind = ? AND sequence NOT IN "
            "(SELECT sequence FROM reports WHERE kind = ? ORDER BY sequence DESC LIMIT ?)",
            (kind, kind, self._retention),
        )

    # ------------------------------------------------------------------ #
    # Lesen
    # ------------------------------------------------------------------ #
    def latest(self, kind: str) -> StoredReport | None:
        """Gibt den neuesten gespeicherten Report einer Art zurück (oder ``None``)."""
        with self._lock:
            try:
                row = self._connection.execute(
                    "SELECT * FROM reports WHERE kind = ? ORDER BY sequence DESC LIMIT 1",
                    (kind,),
                ).fetchone()
            except sqlite3.Error as error:  # pragma: no cover - Infrastrukturfehler
                raise PersistenceError(f"Report konnte nicht gelesen werden: {error}") from error
        return self._row_to_report(row) if row is not None else None

    def history(self, kind: str, limit: int = 20) -> tuple[StoredReport, ...]:
        """Gibt die letzten ``limit`` Einträge einer Art zurück (neueste zuerst)."""
        bound = max(int(limit), 0)
        if bound == 0:
            return ()
        with self._lock:
            try:
                rows = self._connection.execute(
                    "SELECT * FROM reports WHERE kind = ? ORDER BY sequence DESC LIMIT ?",
                    (kind, bound),
                ).fetchall()
            except sqlite3.Error as error:  # pragma: no cover - Infrastrukturfehler
                raise PersistenceError(f"Historie konnte nicht gelesen werden: {error}") from error
        return tuple(self._row_to_report(row) for row in rows)

    def kinds(self) -> tuple[str, ...]:
        """Gibt alle Report-Arten zurück, für die Einträge existieren (sortiert)."""
        with self._lock:
            rows = self._connection.execute(
                "SELECT DISTINCT kind FROM reports ORDER BY kind"
            ).fetchall()
        return tuple(str(row["kind"]) for row in rows)

    def count(self, kind: str | None = None) -> int:
        """Zählt gespeicherte Einträge (insgesamt oder je Art)."""
        with self._lock:
            if kind is None:
                row = self._connection.execute("SELECT COUNT(*) AS n FROM reports").fetchone()
            else:
                row = self._connection.execute(
                    "SELECT COUNT(*) AS n FROM reports WHERE kind = ?", (kind,)
                ).fetchone()
        return int(row["n"])

    @property
    def revision(self) -> int:
        """Monoton steigende Revision (= höchste vergebene ``sequence``).

        Ändert sich bei **jeder** Speicherung. Eignet sich als Cache-Schlüssel:
        gleiche Revision ⇒ unveränderter Datenbestand.
        """
        return self._revision

    def close(self) -> None:
        """Schließt die Datenbankverbindung (für Tests/Shutdown)."""
        with self._lock:
            self._connection.close()

    @staticmethod
    def _row_to_report(row: sqlite3.Row) -> StoredReport:
        """Wandelt eine Datenbankzeile in einen :class:`StoredReport` um."""
        return StoredReport(
            kind=str(row["kind"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            payload=json.loads(str(row["payload"])),
            sequence=int(row["sequence"]),
            report_version=int(row["report_version"]),
        )


__all__ = ["ReportStore"]
