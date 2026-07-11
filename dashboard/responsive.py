"""Responsive-Layout-Anpassung (reine Anzeige).

Passt die Regionen einer Seite an die Geräteklasse an. Ziel sind Desktop,
Tablet, UltraWide und 4K (Smartphone ist kein Ziel dieses Sprints). Es findet
**keine** Fachlogik statt – nur eine Umordnung der Widget-Regionen.
"""

from __future__ import annotations

from dashboard.router import REGIONS
from dashboard.state import DeviceClass

_COLUMN_COUNT: dict[DeviceClass, int] = {
    DeviceClass.TABLET: 1,
    DeviceClass.DESKTOP: 3,
    DeviceClass.ULTRAWIDE: 4,
    DeviceClass.UHD_4K: 4,
}


def column_count(device: DeviceClass) -> int:
    """Anzahl der Layout-Spalten für eine Geräteklasse."""
    return _COLUMN_COUNT.get(device, 3)


def adapt_regions(
    regions: dict[str, tuple[str, ...]], device: DeviceClass
) -> dict[str, tuple[str, ...]]:
    """Ordnet die Widget-Regionen für die Geräteklasse um.

    * Tablet: eine Spalte – alle Widgets nacheinander in ``center``.
    * Desktop/UltraWide/4K: dreispaltiges Layout unverändert (mehr Breite).
    """
    if device is DeviceClass.TABLET:
        ordered: list[str] = []
        for region in REGIONS:
            ordered.extend(regions.get(region, ()))
        return {"center": tuple(ordered)}
    return {region: regions.get(region, ()) for region in REGIONS}
