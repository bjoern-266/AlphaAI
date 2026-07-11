"""System-Status- und Fehler-/Ladezustände (nur Anzeige).

Diese Helfer leiten aus der **Anwesenheit** und Gültigkeit vorhandener Reports
einen Anzeige-Status ab (online / no_data / offline / degraded). Das ist reines
Ablesen von Vorhandensein – **keine** Fachlogik und **keine** Berechnung.
"""

from __future__ import annotations

from dashboard.state import SystemStatus
from models.dashboard import (
    TONE_DANGER,
    TONE_INFO,
    TONE_NEUTRAL,
    TONE_SUCCESS,
    TONE_WARNING,
    StatusItem,
)

_STATUS_TONE: dict[SystemStatus, str] = {
    SystemStatus.ONLINE: TONE_SUCCESS,
    SystemStatus.OFFLINE: TONE_DANGER,
    SystemStatus.NO_DATA: TONE_WARNING,
    SystemStatus.DEGRADED: TONE_INFO,
}


def module_status(present: bool, valid: bool = True, has_data: bool = True) -> SystemStatus:
    """Leitet den Status eines Moduls aus Vorhandensein/Gültigkeit ab.

    Args:
        present: Ob überhaupt ein Report vorliegt.
        valid: Ob der Report als gültig markiert ist.
        has_data: Ob der Report anzeigbare Daten enthält.
    """
    if not present:
        return SystemStatus.OFFLINE
    if not valid:
        return SystemStatus.DEGRADED
    if not has_data:
        return SystemStatus.NO_DATA
    return SystemStatus.ONLINE


def status_tone(status: SystemStatus) -> str:
    """Gibt die semantische Tönung zu einem Status zurück."""
    return _STATUS_TONE.get(status, TONE_NEUTRAL)


def status_item(name: str, status: SystemStatus) -> StatusItem:
    """Baut einen :class:`StatusItem` aus Name und Status."""
    return StatusItem(name=name, status=status.value, tone=status_tone(status))
