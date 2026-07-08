"""Marktdaten-Engine – oberste Schnittstelle der Data Layer.

Die :class:`MarketDataEngine` bietet bequeme, fachnahe Methoden zum Laden von
Marktdaten und delegiert die eigentliche Arbeit an das Repository. Sie kennt
**ausschließlich** das Repository (nie einen Provider direkt). Der spätere
Scanner wird wiederum ausschließlich diese Engine kennen.

Aufgaben der Engine:

- Standardwerte für Zeitraum/Intervall aus der Konfiguration anwenden.
- Symbol- und Universums-basierte Anfragen in :class:`MarketRequest` übersetzen.
"""

from __future__ import annotations

from collections.abc import Callable

from core.config import Settings
from core.logging_config import get_logger
from data.market_request import MarketRequest
from data.market_result import MarketResult
from data.universe import Universe, get_universe
from repositories.market_repository import MarketRepository

_logger = get_logger(__name__)

# Auflösefunktion für Universen (injizierbar für Tests).
UniverseResolver = Callable[[str], Universe]


class MarketDataEngine:
    """Fachnahe Zugriffsschicht auf Marktdaten.

    Args:
        repository: Das zu verwendende Marktdaten-Repository.
        settings: Projektkonfiguration (liefert Standard-Intervall/-Zeitraum).
        universe_resolver: Funktion, die einen Universumsschlüssel auflöst.
            Standard ist :func:`data.universe.get_universe`; für Tests kann eine
            Attrappe injiziert werden.
    """

    def __init__(
        self,
        repository: MarketRepository,
        settings: Settings,
        universe_resolver: UniverseResolver | None = None,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._resolve_universe = universe_resolver or self._default_resolver

    @staticmethod
    def _default_resolver(key: str) -> Universe:
        """Standard-Auflösung eines Universums über die Konfigurationsdatei."""
        return get_universe(key)

    def get(self, request: MarketRequest) -> MarketResult:
        """Führt eine bereits gebaute Anfrage aus.

        Args:
            request: Die auszuführende Marktdatenanfrage.

        Returns:
            Das :class:`MarketResult` des Repositories.
        """
        return self._repository.get_market_data(request)

    def get_symbols(
        self,
        symbols: list[str] | tuple[str, ...],
        timeframe: str | None = None,
        interval: str | None = None,
        market: str = "default",
        use_cache: bool = True,
    ) -> MarketResult:
        """Lädt Daten für eine Symbolliste.

        Fehlende Werte für ``timeframe``/``interval`` werden aus der
        Konfiguration ergänzt.

        Args:
            symbols: Zu ladende Symbole.
            timeframe: Zeitraum/Rückschau (Standard aus Konfiguration).
            interval: Kerzenintervall (Standard aus Konfiguration).
            market: Markt-/Universumsbezeichnung.
            use_cache: Ob der Cache verwendet werden darf.

        Returns:
            Das :class:`MarketResult`.
        """
        request = MarketRequest(
            symbols=tuple(symbols),
            timeframe=timeframe or self._settings.data.default_timeframe,
            interval=interval or self._settings.data.default_interval,
            market=market,
            use_cache=use_cache,
        )
        return self._repository.get_market_data(request)

    def get_universe(
        self,
        universe_key: str,
        timeframe: str | None = None,
        interval: str | None = None,
        use_cache: bool = True,
    ) -> MarketResult:
        """Lädt Daten für alle Symbole eines Universums.

        Args:
            universe_key: Schlüssel des Universums (z. B. ``"dax"``).
            timeframe: Zeitraum/Rückschau (Standard aus Konfiguration).
            interval: Kerzenintervall (Standard aus Konfiguration).
            use_cache: Ob der Cache verwendet werden darf.

        Returns:
            Das :class:`MarketResult` für die Symbole des Universums.
        """
        universe = self._resolve_universe(universe_key)
        _logger.info("Lade Universum '%s' (%d Symbole).", universe.name, universe.size)
        return self.get_symbols(
            symbols=universe.symbols,
            timeframe=timeframe,
            interval=interval,
            market=universe.key,
            use_cache=use_cache,
        )
