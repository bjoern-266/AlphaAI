"""In-Memory-Cache mit Ablaufzeit (TTL) für Marktdaten.

Der Cache verhindert wiederholte, teure Abfragen bei Datenquellen. Er ist
bewusst einfach gehalten (Speicher, kein Persistenzlayer) und über eine
injizierbare Uhr (``clock``) vollständig testbar – ohne echtes Warten.

Es werden drei fachliche Kategorien mit eigener TTL unterschieden
(:class:`CacheCategory`): historische Daten, Intraday-Daten und Tickerlisten.
Die konkreten TTL-Werte stammen aus der Konfiguration (``[data.cache]``) und
sind nicht im Code hartcodiert.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.config import CacheConfig


class CacheCategory(Enum):
    """Fachliche Kategorie eines Cache-Eintrags mit eigener TTL."""

    HISTORICAL = "historical"
    INTRADAY = "intraday"
    TICKERLIST = "tickerlist"


@dataclass(slots=True)
class _CacheEntry:
    """Interner Cache-Eintrag mit Ablaufzeitpunkt."""

    value: Any
    expires_at: float


class TTLCache:
    """Thread-sicherer Cache mit kategoriespezifischer Ablaufzeit.

    Args:
        config: Cache-Konfiguration mit den TTL-Werten je Kategorie.
        clock: Funktion, die die aktuelle Zeit in Sekunden liefert. Für Tests
            kann eine kontrollierbare Uhr injiziert werden (Dependency
            Injection). Standard ist :func:`time.monotonic`.
    """

    def __init__(self, config: CacheConfig, clock: Callable[[], float] = time.monotonic) -> None:
        self._config = config
        self._clock = clock
        self._store: dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()

    def ttl_for(self, category: CacheCategory) -> int:
        """Gibt die konfigurierte TTL (in Sekunden) für eine Kategorie zurück."""
        mapping = {
            CacheCategory.HISTORICAL: self._config.historical_ttl_seconds,
            CacheCategory.INTRADAY: self._config.intraday_ttl_seconds,
            CacheCategory.TICKERLIST: self._config.tickerlist_ttl_seconds,
        }
        return mapping[category]

    def get(self, key: str) -> Any | None:
        """Gibt den zwischengespeicherten Wert zurück oder ``None``.

        Abgelaufene Einträge werden entfernt und als Fehltreffer behandelt.
        Ist der Cache deaktiviert, wird stets ``None`` zurückgegeben.
        """
        if not self._config.enabled:
            return None
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if self._clock() >= entry.expires_at:
                del self._store[key]
                return None
            return entry.value

    def set(self, key: str, value: Any, category: CacheCategory) -> None:
        """Legt einen Wert mit der TTL der angegebenen Kategorie ab.

        Ist der Cache deaktiviert, wird nichts gespeichert.
        """
        if not self._config.enabled:
            return
        ttl = self.ttl_for(category)
        with self._lock:
            self._store[key] = _CacheEntry(value=value, expires_at=self._clock() + ttl)

    def invalidate(self, key: str) -> None:
        """Entfernt einen einzelnen Eintrag, falls vorhanden."""
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        """Leert den gesamten Cache."""
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        """Gibt die Anzahl aktuell gespeicherter (auch abgelaufener) Einträge zurück."""
        with self._lock:
            return len(self._store)
