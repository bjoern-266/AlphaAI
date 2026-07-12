"""Ergebnis-/Datentypen der Application-Schicht (Re-Export).

Die Definitionen liegen in der Entities-Schicht :mod:`models.application`. Dieses
Modul re-exportiert sie unter dem etablierten Pfad ``engines.application_result`` –
konsistent mit ``engines.operations_result``.
"""

from __future__ import annotations

from models.application import (
    ApiEnvelope,
    ApiError,
    ApiVersion,
    ComponentHealth,
    EndpointInfo,
    HealthReport,
    HealthStatus,
    ReportKind,
    ServiceInfo,
    StoredReport,
)

__all__ = [
    "ApiEnvelope",
    "ApiError",
    "ApiVersion",
    "ComponentHealth",
    "EndpointInfo",
    "HealthReport",
    "HealthStatus",
    "ReportKind",
    "ServiceInfo",
    "StoredReport",
]
