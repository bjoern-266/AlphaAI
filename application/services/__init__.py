"""Dienste der Application-Schicht.

Die Dienste **lesen** gespeicherte Reports und stellen sie in der von der API
benötigten Form bereit. Sie berechnen nichts und ändern keine Fachdaten:

* :class:`ReportService` – liest gespeicherte Reports und filtert (z. B. Ticker),
* :class:`SystemService` – liefert Version/Status des Dienstes,
* :class:`BackgroundService` – betreibt den Hintergrunddienst (Takt + Persistenz).
"""

from __future__ import annotations

from application.services.background_service import BackgroundService
from application.services.report_service import ReportService
from application.services.system_service import SystemService

__all__ = ["BackgroundService", "ReportService", "SystemService"]
