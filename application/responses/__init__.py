"""Einheitliche API-Antwort-Hüllen (Envelope).

Jede API-Antwort – Erfolg wie Fehler – erhält dieselbe äußere Struktur
(:class:`models.application.ApiEnvelope`). Das hält die API stabil, gut
versionierbar und erleichtert die spätere Android-Anbindung (Sprint 18).
"""

from __future__ import annotations

from application.responses.envelope import (
    error_envelope,
    error_from_exception,
    success_envelope,
)

__all__ = ["success_envelope", "error_envelope", "error_from_exception"]
