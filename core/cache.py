"""Generischer, größenbegrenzter In-Memory-Cache (FIFO-Verdrängung).

:class:`Cache` bündelt die zuvor mehrfach (Indicator/Pattern/Strategy/Score)
duplizierte Cache-Logik an **einer** Stelle. Der Cache speichert Werte eines
beliebigen Typs ``T`` unter einem vom Aufrufer gebildeten Schlüssel, verdrängt
bei Überschreiten der Kapazität den ältesten Eintrag (FIFO) und zählt
Treffer/Fehltreffer für Diagnose und Tests.

Die konkreten Engine-Caches erben von dieser Basis und legen lediglich den
Wertetyp fest; ihr öffentliches Verhalten (``get``/``set``/``clear``/``hits``/
``misses``/``len``) bleibt unverändert.

Abgrenzung: Der TTL-basierte Marktdaten-Cache (:class:`data.cache.TTLCache`)
bleibt eigenständig, da er kategoriespezifische Ablaufzeiten und
Thread-Sicherheit benötigt – ein anderes Verhalten als dieser FIFO-Cache.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Generic, TypeVar

from core.exceptions import CacheCapacityError

T = TypeVar("T")


class Cache(Generic[T]):
    """Größenbegrenzter Cache mit FIFO-Verdrängung und Trefferzählung.

    Args:
        capacity: Maximale Anzahl gespeicherter Einträge. Beim Überschreiten
            wird der älteste Eintrag verdrängt (FIFO).

    Raises:
        CacheCapacityError: Wenn ``capacity`` kleiner als 1 ist.
    """

    def __init__(self, capacity: int = 128) -> None:
        if capacity < 1:
            raise CacheCapacityError("capacity muss mindestens 1 sein.")
        self._capacity = capacity
        self._store: OrderedDict[str, T] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> T | None:
        """Gibt den gespeicherten Wert zurück und zählt Treffer/Fehltreffer."""
        if key in self._store:
            self.hits += 1
            return self._store[key]
        self.misses += 1
        return None

    def set(self, key: str, value: T) -> None:
        """Legt einen Wert ab und verdrängt bei Bedarf den ältesten Eintrag."""
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        if len(self._store) > self._capacity:
            self._store.popitem(last=False)

    def clear(self) -> None:
        """Leert den Cache (Zähler bleiben erhalten)."""
        self._store.clear()

    def __len__(self) -> int:
        """Anzahl aktuell gespeicherter Einträge."""
        return len(self._store)
