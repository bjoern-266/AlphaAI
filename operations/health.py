"""Health: leitet den Gesundheitszustand des Systems ab.

Bewertet aus Fehlerzahl, Scan-Zahl und Heartbeat einen Gesamtzustand
(``OK``/``DEGRADED``/``ERROR``). Reine Ableitung aus vorhandenen Kennzahlen –
**keine** Fachlogik. Der Schwellenwert ist konfigurierbar.
"""

from __future__ import annotations

from models.operations import Heartbeat, SystemHealth


def assess_health(
    error_count: int,
    scan_count: int,
    heartbeat: Heartbeat | None = None,
    degraded_ratio: float = 0.3,
) -> SystemHealth:
    """Bewertet den Gesamtzustand.

    * ``ERROR``: der Heartbeat ist tot.
    * ``DEGRADED``: es gab Fehler, aber noch keinen erfolgreichen Scan, **oder**
      der Fehleranteil überschreitet ``degraded_ratio``.
    * ``OK``: sonst.
    """
    if heartbeat is not None and not heartbeat.alive:
        return SystemHealth.ERROR
    total = scan_count + error_count
    if error_count > 0 and scan_count == 0:
        return SystemHealth.DEGRADED
    if total > 0 and error_count / total > degraded_ratio:
        return SystemHealth.DEGRADED
    return SystemHealth.OK
