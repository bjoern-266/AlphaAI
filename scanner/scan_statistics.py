"""Statistik eines Scan-Laufs.

:class:`ScanStatistics` sammelt Kennzahlen während eines Scans: Zeiten,
Laufzeit, Anzahl Symbole, Provider, Cache-Treffer/-Fehltreffer sowie Fehler.
Die Zeitquelle ist injizierbar, damit Laufzeiten in Tests deterministisch
prüfbar sind.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any


def _utcnow() -> datetime:
    """Gibt die aktuelle Zeit als zeitzonenbewusste UTC-Zeit zurück."""
    return datetime.now(UTC)


class ScanStatistics:
    """Sammelt Kennzahlen eines Scan-Laufs.

    Args:
        provider: Name des verwendeten Providers (kann später aktualisiert
            werden, sobald das erste Ergebnis vorliegt).
        now_fn: Funktion, die die aktuelle Zeit liefert (injizierbar für Tests).
    """

    def __init__(self, provider: str = "unknown", now_fn: Callable[[], datetime] = _utcnow) -> None:
        self._now = now_fn
        self.provider = provider
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.symbol_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.error_count = 0
        self.error_messages: list[str] = []

    def start(self) -> None:
        """Markiert den Startzeitpunkt des Scans."""
        self.start_time = self._now()

    def finish(self) -> None:
        """Markiert den Endzeitpunkt des Scans."""
        self.end_time = self._now()

    def record_symbol(self, cache_hit: bool, error_message: str | None = None) -> None:
        """Erfasst ein verarbeitetes Symbol.

        Args:
            cache_hit: Ob die Daten aus dem Cache stammten.
            error_message: Fehlermeldung, falls beim Symbol ein Fehler auftrat.
        """
        self.symbol_count += 1
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        if error_message:
            self.error_count += 1
            self.error_messages.append(error_message)

    @property
    def runtime_seconds(self) -> float:
        """Laufzeit in Sekunden (0.0, solange Start oder Ende fehlt)."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Gibt die Statistik als serialisierbares Wörterbuch zurück."""
        return {
            "provider": self.provider,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "runtime_seconds": self.runtime_seconds,
            "symbol_count": self.symbol_count,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "error_count": self.error_count,
        }
