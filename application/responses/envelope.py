"""Bau der einheitlichen API-Antwort-Hüllen.

Diese Funktionen erzeugen aus Nutzdaten bzw. Fehlern eine
:class:`~models.application.ApiEnvelope`. Sie sind bewusst rein
(seiteneffektfrei) und framework-unabhängig – die konkrete HTTP-Auslieferung
übernimmt die API-Schicht.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from application.exceptions import ApplicationError
from models.application import ApiEnvelope, ApiError


def _base_meta(api_version: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Baut die Standard-Metadaten jeder Antwort (Zeitstempel, API-Version)."""
    meta: dict[str, Any] = {
        "api_version": api_version,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    if extra:
        meta.update(extra)
    return meta


def success_envelope(
    data: Any,
    *,
    api_version: str = "v1",
    meta: dict[str, Any] | None = None,
) -> ApiEnvelope:
    """Erzeugt eine Erfolgs-Hülle um bereits JSON-fähige Nutzdaten.

    Args:
        data: Die auszuliefernden Nutzdaten (bereits serialisiert).
        api_version: Aktive API-Version (für die Metadaten).
        meta: Optionale Zusatz-Metadaten (z. B. ``kind``, ``cache``).

    Returns:
        Eine :class:`ApiEnvelope` mit ``ok=True``.
    """
    return ApiEnvelope(ok=True, data=data, error=None, meta=_base_meta(api_version, meta))


def error_envelope(
    *,
    status: int,
    code: str,
    message: str,
    detail: dict[str, Any] | None = None,
    api_version: str = "v1",
) -> ApiEnvelope:
    """Erzeugt eine Fehler-Hülle mit strukturierter Fehlerinformation.

    Args:
        status: HTTP-Statuscode.
        code: Stabiler, maschinenlesbarer Fehlercode.
        message: Menschenlesbare Fehlermeldung.
        detail: Optionale Zusatzinformationen.
        api_version: Aktive API-Version (für die Metadaten).

    Returns:
        Eine :class:`ApiEnvelope` mit ``ok=False`` und gefülltem ``error``.
    """
    error = ApiError(status=status, code=code, message=message, detail=detail or {})
    return ApiEnvelope(ok=False, data=None, error=error, meta=_base_meta(api_version))


def error_from_exception(error: ApplicationError, *, api_version: str = "v1") -> ApiEnvelope:
    """Erzeugt eine Fehler-Hülle aus einem :class:`ApplicationError`.

    Args:
        error: Der aufgetretene Application-Fehler (trägt ``status``/``code``).
        api_version: Aktive API-Version (für die Metadaten).

    Returns:
        Eine :class:`ApiEnvelope` mit ``ok=False``.
    """
    return error_envelope(
        status=error.status,
        code=error.code,
        message=error.message,
        detail=error.detail,
        api_version=api_version,
    )


__all__ = ["success_envelope", "error_envelope", "error_from_exception"]
