"""Marktuhr: bestimmt die aktuelle Phase und die Countdowns je Markt.

Berechnet aus den Marktsitzungen und einem Zeitpunkt (UTC) den Zustand jedes
Marktes (Phase, geöffnet/geschlossen, nächste Phase, Countdown) sowie den als
nächstes öffnenden Markt. Sommer-/Winterzeit wird über die IANA-Zeitzone
automatisch berücksichtigt. Es findet **keine** Fachlogik statt – nur Zeitlogik.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from models.operations import MarketClock, MarketState
from operations.market_sessions import MarketSession, Phase


def _local_midnight(local: datetime) -> datetime:
    """Mitternacht des lokalen Tages (mit Zeitzone)."""
    return local.replace(hour=0, minute=0, second=0, microsecond=0)


def _phase_datetime(local: datetime, phase: Phase, day_offset: int = 0) -> datetime:
    """Zeitpunkt des Phasenbeginns am lokalen Tag (+ Offset), in UTC."""
    start = _local_midnight(local) + timedelta(days=day_offset, minutes=phase.start_minute)
    return start.astimezone(UTC)


def compute_market_state(session: MarketSession, now: datetime) -> MarketState:
    """Bestimmt den Zustand eines Marktes zum Zeitpunkt ``now`` (UTC)."""
    tz = ZoneInfo(session.timezone)
    local = now.astimezone(tz)
    minute = local.hour * 60 + local.minute
    phases = session.phases

    current_index: int | None = None
    for index, phase in enumerate(phases):
        if phase.start_minute <= minute:
            current_index = index

    if current_index is None:
        # Vor der ersten Phase des Tages: es gilt die letzte Phase (von gestern);
        # der nächste Wechsel ist die erste Phase von heute.
        current = phases[-1]
        next_phase = phases[0]
        next_change = _phase_datetime(local, next_phase, day_offset=0)
    else:
        current = phases[current_index]
        if current_index + 1 < len(phases):
            next_phase = phases[current_index + 1]
            next_change = _phase_datetime(local, next_phase, day_offset=0)
        else:
            next_phase = phases[0]
            next_change = _phase_datetime(local, next_phase, day_offset=1)

    seconds = int((next_change - now).total_seconds())
    return MarketState(
        key=session.key,
        title=session.title,
        timezone=session.timezone,
        phase=current.name,
        is_open=current.is_open,
        next_phase=next_phase.name,
        next_change_at=next_change,
        seconds_to_next=seconds,
    )


def next_open_at(session: MarketSession, now: datetime) -> datetime | None:
    """Nächster Zeitpunkt, zu dem der Markt in eine **offene** Phase wechselt."""
    tz = ZoneInfo(session.timezone)
    local = now.astimezone(tz)
    minute = local.hour * 60 + local.minute
    open_phases = [phase for phase in session.phases if phase.is_open]
    if not open_phases:
        return None
    for phase in open_phases:
        if phase.start_minute > minute:
            return _phase_datetime(local, phase, day_offset=0)
    return _phase_datetime(local, open_phases[0], day_offset=1)


def build_market_clock(sessions: Sequence[MarketSession], now: datetime) -> MarketClock:
    """Baut die :class:`MarketClock` für alle Märkte zum Zeitpunkt ``now``."""
    states = tuple(compute_market_state(session, now) for session in sessions)
    next_market = ""
    next_at: datetime | None = None
    for session in sessions:
        candidate = next_open_at(session, now)
        if candidate is not None and (next_at is None or candidate < next_at):
            next_at = candidate
            next_market = session.key
    return MarketClock(
        as_of=now, markets=states, next_open_market=next_market, next_open_at=next_at
    )
