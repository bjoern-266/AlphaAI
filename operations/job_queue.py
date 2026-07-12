"""Job-Queue: serialisiert Jobs und verhindert parallele Vollanalysen.

Stellt sicher, dass **nur ein** Discovery-Job gleichzeitig läuft, **keine**
parallelen Vollanalysen stattfinden und **doppelte** Jobs abgewiesen werden. Da
die Ausführung derzeit synchron erfolgt (noch keine Parallelisierung), garantiert
die Queue die Serialisierung und die Duplikat-/Exklusiv-Prüfung. Ein Fehler eines
Jobs darf den Scheduler **niemals** blockieren (die Queue kennt keine Fachlogik).
"""

from __future__ import annotations

from models.operations import ScheduledJob

# Job-Arten, von denen höchstens eine gleichzeitig laufen/warten darf.
_DEFAULT_EXCLUSIVE = ("discovery",)


class JobQueue:
    """Serialisierende Warteschlange mit Exklusiv- und Duplikatschutz.

    Args:
        exclusive_types: Job-Arten, die exklusiv sind (Standard: ``discovery``).
    """

    def __init__(self, exclusive_types: tuple[str, ...] = _DEFAULT_EXCLUSIVE) -> None:
        self._exclusive = exclusive_types
        self._pending: list[ScheduledJob] = []
        self._running: ScheduledJob | None = None

    @property
    def size(self) -> int:
        """Anzahl wartender Jobs."""
        return len(self._pending)

    @property
    def running(self) -> ScheduledJob | None:
        """Der aktuell laufende Job (oder ``None``)."""
        return self._running

    def _has_type(self, job_type: str) -> bool:
        """Ob eine Job-Art bereits läuft oder wartet."""
        if self._running is not None and self._running.job_type == job_type:
            return True
        return any(job.job_type == job_type for job in self._pending)

    def _known_name(self, name: str) -> bool:
        """Ob ein Job-Name bereits läuft oder wartet."""
        if self._running is not None and self._running.name == name:
            return True
        return any(job.name == name for job in self._pending)

    def submit(self, job: ScheduledJob) -> bool:
        """Nimmt einen Job in die Queue auf.

        Returns:
            ``True``, wenn der Job aufgenommen wurde; ``False`` bei Duplikat oder
            wenn eine exklusive Art bereits läuft/wartet.
        """
        if self._known_name(job.name):
            return False
        if job.job_type in self._exclusive and self._has_type(job.job_type):
            return False
        self._pending.append(job)
        return True

    def start_next(self) -> ScheduledJob | None:
        """Startet den nächsten wartenden Job (nur einer gleichzeitig)."""
        if self._running is not None:
            return None
        if not self._pending:
            return None
        self._running = self._pending.pop(0)
        return self._running

    def complete(self) -> None:
        """Meldet den laufenden Job als beendet (Erfolg **oder** Fehler)."""
        self._running = None

    def clear(self) -> None:
        """Leert die Warteschlange (und den laufenden Job)."""
        self._pending.clear()
        self._running = None
