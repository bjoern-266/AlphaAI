"""Konkrete Fehlerklassen der Application-Schicht.

Jede Fehlerklasse trägt einen stabilen, maschinenlesbaren ``code`` und einen
HTTP-``status``. Die API-Schicht bildet daraus ohne weitere Fallunterscheidung
eine einheitliche Fehlerantwort (siehe ``application.responses``).
"""

from __future__ import annotations

from core.exceptions import AlphaAIError


class ApplicationError(AlphaAIError):
    """Basisklasse aller Fehler der Application-/API-Schicht.

    Attributes:
        code: Stabiler, maschinenlesbarer Fehlercode.
        status: Zugeordneter HTTP-Statuscode.
    """

    code: str = "application_error"
    status: int = 500

    def __init__(self, message: str, detail: dict | None = None) -> None:
        """Erzeugt den Fehler mit Meldung und optionalem Detail-Kontext."""
        super().__init__(message)
        self.message = message
        self.detail: dict = detail or {}


class InvalidRequestError(ApplicationError):
    """Ein Request ist ungültig (falsche/fehlende Parameter, ungültiger Pfad)."""

    code = "invalid_request"
    status = 400


class ReportNotFoundError(ApplicationError):
    """Der angeforderte Report (oder Ticker) ist nicht vorhanden."""

    code = "not_found"
    status = 404


class ServiceUnavailableError(ApplicationError):
    """Der Dienst kann die Anfrage vorübergehend nicht bedienen.

    Beispiel: Es liegt noch kein erfolgreicher Scan vor oder die Persistenz ist
    nicht erreichbar. Der Dienst selbst bleibt jedoch am Leben (Recovery).
    """

    code = "service_unavailable"
    status = 503


class PersistenceError(ApplicationError):
    """Ein Fehler beim dauerhaften Speichern oder Laden von Reports."""

    code = "persistence_error"
    status = 500


class AuthenticationError(ApplicationError):
    """Zugriff verweigert (aktuell: Zugriff nur von lokalem Host erlaubt)."""

    code = "unauthorized"
    status = 401


__all__ = [
    "ApplicationError",
    "AuthenticationError",
    "InvalidRequestError",
    "PersistenceError",
    "ReportNotFoundError",
    "ServiceUnavailableError",
]
