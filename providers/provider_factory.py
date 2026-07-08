"""Fabrik zur Erzeugung von Providern anhand ihres Namens.

Die Fabrik ist die einzige Stelle, an der konkrete Provider-Klassen bekannt
sind. Repository und Engine fragen Provider ausschließlich über ihren Namen an
und bleiben so von konkreten Implementierungen entkoppelt.

Aktuell implementiert: ``yahoo``.

Vorbereitet (noch nicht implementiert): ``finnhub``, ``polygon``,
``alphavantage``, ``iex``. Diese Namen sind bekannt und dokumentiert; ihr
Abruf löst bewusst einen klaren :class:`ProviderNotImplementedError` aus,
statt stillschweigend falsche Daten zu liefern.
"""

from __future__ import annotations

from collections.abc import Callable

from providers.base_provider import BaseProvider, ProviderError, ProviderNotImplementedError
from providers.yahoo_provider import YahooProvider

# Registry der implementierten Provider: Name -> Erzeugungsfunktion.
_IMPLEMENTED: dict[str, Callable[[], BaseProvider]] = {
    "yahoo": YahooProvider,
}

# Vorbereitete, aber noch nicht implementierte Provider.
# Der Wert beschreibt, was zur Implementierung nötig sein wird.
_PLANNED: dict[str, str] = {
    "finnhub": "Finnhub-API (benötigt späteren API-Schlüssel in der Konfiguration).",
    "polygon": "Polygon.io-API (benötigt späteren API-Schlüssel).",
    "alphavantage": "Alpha-Vantage-API (benötigt späteren API-Schlüssel).",
    "iex": "IEX-Cloud-API (benötigt späteren API-Schlüssel).",
}


def available_providers() -> list[str]:
    """Gibt die Namen aller implementierten Provider zurück."""
    return sorted(_IMPLEMENTED)


def planned_providers() -> list[str]:
    """Gibt die Namen aller vorbereiteten, noch nicht implementierten Provider zurück."""
    return sorted(_PLANNED)


def create_provider(name: str) -> BaseProvider:
    """Erzeugt einen Provider anhand seines Namens.

    Args:
        name: Provider-Name (Groß-/Kleinschreibung egal), z. B. ``"yahoo"``.

    Returns:
        Eine einsatzbereite Provider-Instanz.

    Raises:
        ProviderNotImplementedError: Wenn der Provider zwar vorgesehen, aber
            noch nicht implementiert ist.
        ProviderError: Wenn der Name gänzlich unbekannt ist.
    """
    key = name.strip().lower()
    if key in _IMPLEMENTED:
        return _IMPLEMENTED[key]()
    if key in _PLANNED:
        raise ProviderNotImplementedError(
            f"Provider '{key}' ist vorbereitet, aber noch nicht implementiert. "
            f"Geplant: {_PLANNED[key]}"
        )
    raise ProviderError(
        f"Unbekannter Provider '{name}'. Verfügbar: {', '.join(available_providers())}."
    )
