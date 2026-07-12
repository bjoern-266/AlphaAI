"""Heartbeat: bestimmt die „Lebendigkeit" des Systems.

Aus dem Zeitpunkt des letzten Herzschlags und einem Intervall wird abgeleitet, ob
das System noch als lebendig gilt. Reine Zeitlogik – **keine** Fachlogik.
"""

from __future__ import annotations

from datetime import datetime

from models.operations import Heartbeat


def build_heartbeat(
    last_beat_at: datetime | None, now: datetime, interval_seconds: int = 60
) -> Heartbeat:
    """Baut den :class:`Heartbeat` aus dem letzten Herzschlag und ``now``.

    Das System gilt als lebendig, solange der letzte Herzschlag nicht älter als
    das doppelte Intervall ist.
    """
    if last_beat_at is None:
        return Heartbeat(
            alive=False, last_beat_at=None, age_seconds=None, interval_seconds=interval_seconds
        )
    age = int((now - last_beat_at).total_seconds())
    alive = 0 <= age <= interval_seconds * 2
    return Heartbeat(
        alive=alive, last_beat_at=last_beat_at, age_seconds=age, interval_seconds=interval_seconds
    )
