"""Zugriffsrichtlinien der Backend-API (vorbereitet, vorerst lokal).

Eine :class:`AuthPolicy` entscheidet ausschließlich, **ob** eine Anfrage
zugelassen wird. Sie trifft keine Fachentscheidung und verändert keine Daten.
Die Standardrichtlinie im produktiven Betrieb ist :class:`LocalOnlyPolicy`:
sie lässt nur Anfragen vom lokalen Host (Loopback) zu.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from application.exceptions import AuthenticationError

# Als lokal geltende Absender-Adressen (IPv4/IPv6-Loopback und leerer Wert).
_LOCAL_HOSTS = frozenset({"127.0.0.1", "::1", "localhost", ""})


@dataclass(frozen=True, slots=True)
class AuthContext:
    """Kontext einer eingehenden Anfrage für die Zugriffsprüfung.

    Attributes:
        client_host: Absender-Adresse (IP/Hostname) oder leer, falls unbekannt.
        token: Optionales Zugriffstoken (für spätere Verfahren vorbereitet).
        headers: Weitere Kopfzeilen (für spätere Verfahren vorbereitet).
    """

    client_host: str = ""
    token: str = ""
    headers: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class AuthPolicy(Protocol):
    """Vertrag einer Zugriffsrichtlinie."""

    name: str

    def authorize(self, context: AuthContext) -> None:
        """Lässt die Anfrage zu oder wirft :class:`AuthenticationError`."""
        ...


class LocalOnlyPolicy:
    """Erlaubt ausschließlich Anfragen vom lokalen Host (Loopback).

    Args:
        allowed_hosts: Optionale Erweiterung der als lokal geltenden Adressen.
    """

    name = "local_only"

    def __init__(self, allowed_hosts: frozenset[str] | None = None) -> None:
        self._allowed = _LOCAL_HOSTS | (allowed_hosts or frozenset())

    def authorize(self, context: AuthContext) -> None:
        """Lässt nur lokale Absender zu.

        Raises:
            AuthenticationError: Wenn der Absender nicht als lokal gilt.
        """
        host = (context.client_host or "").strip().lower()
        if host not in self._allowed:
            raise AuthenticationError(
                "Zugriff nur vom lokalen Host erlaubt.",
                detail={"client_host": context.client_host},
            )


class OpenPolicy:
    """Lässt jede Anfrage zu (nur für Tests/Entwicklung, nicht für Produktion)."""

    name = "open"

    def authorize(self, context: AuthContext) -> None:
        """Lässt jede Anfrage zu (keine Prüfung)."""
        return None


__all__ = ["AuthContext", "AuthPolicy", "LocalOnlyPolicy", "OpenPolicy"]
