"""System-State: fasst den Systemzustand zusammen (reine Aggregation).

Bündelt Health, Heartbeat, laufenden Job, Queue-Größe und Zähler zu einem
:class:`~models.operations.SystemState`. Enthält **keine** Fachlogik.
"""

from __future__ import annotations

from models.operations import Heartbeat, SystemState
from operations.health import assess_health


def build_system_state(
    heartbeat: Heartbeat,
    running_job: str | None,
    queue_size: int,
    scan_count: int,
    error_count: int,
    last_error: str = "",
    uptime_seconds: int | None = None,
    degraded_ratio: float = 0.3,
) -> SystemState:
    """Baut den :class:`SystemState` (inkl. abgeleitetem Health-Zustand)."""
    health = assess_health(error_count, scan_count, heartbeat, degraded_ratio)
    return SystemState(
        health=health,
        heartbeat=heartbeat,
        running_job=running_job,
        queue_size=queue_size,
        scan_count=scan_count,
        error_count=error_count,
        last_error=last_error,
        uptime_seconds=uptime_seconds,
    )
