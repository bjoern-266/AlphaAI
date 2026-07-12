"""Fehlerhierarchie der Application-Schicht.

Alle Fehler der Application-/API-Schicht stammen von :class:`ApplicationError`
ab, die ihrerseits von der projektweiten :class:`core.exceptions.AlphaAIError`
erbt. So kann aufrufender Code gezielt Application-Fehler abfangen, ohne breite
``except Exception``-Blöcke zu verwenden.
"""

from __future__ import annotations

from application.exceptions.errors import (
    ApplicationError,
    AuthenticationError,
    InvalidRequestError,
    PersistenceError,
    ReportNotFoundError,
    ServiceUnavailableError,
)

__all__ = [
    "ApplicationError",
    "AuthenticationError",
    "InvalidRequestError",
    "PersistenceError",
    "ReportNotFoundError",
    "ServiceUnavailableError",
]
