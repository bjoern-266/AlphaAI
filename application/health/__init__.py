"""Aggregiertes Health-Monitoring des Backend-Dienstes.

Der :class:`HealthMonitor` liest den zuletzt gespeicherten Operations-Report
sowie Kennzahlen des Speichers/Caches und leitet daraus einen aggregierten
:class:`~models.application.HealthReport` ab (API/Scheduler/Markt/Queue/Cache/
System/Persistenz). Es findet **keine** Berechnung von Fachdaten statt.
"""

from __future__ import annotations

from application.health.health_monitor import HealthMonitor

__all__ = ["HealthMonitor"]
