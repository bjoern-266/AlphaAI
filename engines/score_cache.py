"""Cache für Score-Ergebnisse.

Ein einfacher, größenbegrenzter In-Memory-Cache (FIFO-Verdrängung). Er
speichert :class:`~engines.score_result.ScoreReport`-Objekte unter einem vom
Aufrufer gebildeten Schlüssel und zählt Treffer/Fehltreffer.
"""

from __future__ import annotations

from collections import OrderedDict

from engines.score_result import ScoreReport


class ScoreCache:
    """Größenbegrenzter Cache für Score-Ergebnisse.

    Args:
        capacity: Maximale Anzahl gespeicherter Einträge (FIFO-Verdrängung).
    """

    def __init__(self, capacity: int = 128) -> None:
        if capacity < 1:
            raise ValueError("capacity muss mindestens 1 sein.")
        self._capacity = capacity
        self._store: OrderedDict[str, ScoreReport] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> ScoreReport | None:
        """Gibt den gespeicherten Wert zurück und zählt Treffer/Fehltreffer."""
        if key in self._store:
            self.hits += 1
            return self._store[key]
        self.misses += 1
        return None

    def set(self, key: str, value: ScoreReport) -> None:
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
