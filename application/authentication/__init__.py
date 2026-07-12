"""Vorbereitete Zugriffskontrolle der Backend-API.

Die Architektur ist auf spätere Erweiterungen (Token, Benutzer, Cloud)
vorbereitet, erlaubt aber **vorerst ausschließlich lokalen Zugriff**. Es gibt
keine Benutzerverwaltung, keine Registrierung und keine Cloud-Anbindung.

Der :class:`AuthPolicy`-Vertrag ist die einzige Erweiterungsstelle: neue
Verfahren implementieren ihn, ohne die übrige API zu verändern (Open/Closed).
"""

from __future__ import annotations

from application.authentication.policy import (
    AuthContext,
    AuthPolicy,
    LocalOnlyPolicy,
    OpenPolicy,
)

__all__ = ["AuthContext", "AuthPolicy", "LocalOnlyPolicy", "OpenPolicy"]
