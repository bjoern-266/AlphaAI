"""Job-Historie: speichert die letzten Job-Läufe (neueste zuerst).

Reiner Verlauf – **keine** Fachlogik. Liefert Kennzahlen (Erfolge/Fehler,
durchschnittliche Laufzeit) rein aus den gespeicherten :class:`JobRun`.
"""

from __future__ import annotations

from models.operations import JobRun, JobStatus


class JobHistory:
    """Ringpuffer der letzten Job-Läufe.

    Args:
        limit: Maximale Anzahl gespeicherter Läufe (älteste werden verworfen).
    """

    def __init__(self, limit: int = 100) -> None:
        self._limit = max(limit, 1)
        self._runs: list[JobRun] = []

    def add(self, run: JobRun) -> None:
        """Fügt einen Lauf hinzu (neueste zuerst; begrenzt auf ``limit``)."""
        self._runs.insert(0, run)
        if len(self._runs) > self._limit:
            del self._runs[self._limit :]

    def recent(self, limit: int) -> tuple[JobRun, ...]:
        """Gibt die letzten ``limit`` Läufe zurück (neueste zuerst)."""
        return tuple(self._runs[: max(limit, 0)])

    def all(self) -> tuple[JobRun, ...]:
        """Gibt alle gespeicherten Läufe zurück (neueste zuerst)."""
        return tuple(self._runs)

    def __len__(self) -> int:
        """Anzahl gespeicherter Läufe."""
        return len(self._runs)

    @property
    def success_count(self) -> int:
        """Anzahl erfolgreicher Läufe."""
        return sum(1 for run in self._runs if run.status is JobStatus.SUCCESS)

    @property
    def error_count(self) -> int:
        """Anzahl fehlgeschlagener Läufe."""
        return sum(1 for run in self._runs if run.status is JobStatus.FAILED)

    def average_runtime(self) -> float | None:
        """Durchschnittliche Laufzeit der gespeicherten Läufe (oder ``None``)."""
        durations = [run.duration_seconds for run in self._runs if run.duration_seconds is not None]
        return sum(durations) / len(durations) if durations else None
