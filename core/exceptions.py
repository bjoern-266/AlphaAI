"""Projektweite Fehlerklassen für Alpha AI.

Eine gemeinsame Basisklasse erlaubt es aufrufendem Code, alle fachlichen
Fehler von Alpha AI gezielt abzufangen, ohne breite ``except Exception``
Blöcke verwenden zu müssen.
"""

from __future__ import annotations


class AlphaAIError(Exception):
    """Basisklasse für alle von Alpha AI ausgelösten Fehler."""


class ConfigError(AlphaAIError):
    """Wird ausgelöst, wenn die Konfiguration fehlt oder ungültig ist.

    Beispiele: fehlende ``settings.toml``, fehlende Pflichtfelder oder
    Werte außerhalb des zulässigen Bereichs (z. B. negatives Risiko).
    """
