"""Marktdaten-Repository.

Das Repository ist die zentrale Zugriffsschicht auf Marktdaten. Es kombiniert:

1. **Cache** – vermeidet wiederholte Abfragen (kategoriespezifische TTL).
2. **Provider** – lädt die eigentlichen Daten (austauschbare Datenquelle).
3. **Validator** – prüft die Daten zerstörungsfrei auf Qualitätsprobleme.

Die :class:`~data.market_data_engine.MarketDataEngine` kennt ausschließlich
dieses Repository und nie einen Provider direkt.
"""

from __future__ import annotations

from core.logging_config import get_logger
from data.cache import CacheCategory, TTLCache
from data.market_request import MarketRequest
from data.market_result import MarketResult, MarketStatus
from data.validator import MarketDataValidator
from providers.base_provider import BaseProvider

_logger = get_logger(__name__)


class MarketRepository:
    """Kapselt Provider-Zugriff, Cache und Validierung.

    Args:
        provider: Die zu verwendende Datenquelle.
        cache: TTL-Cache für Ergebnisse.
        validator: Validator zur Qualitätsprüfung der geladenen Daten.
    """

    def __init__(
        self,
        provider: BaseProvider,
        cache: TTLCache,
        validator: MarketDataValidator,
    ) -> None:
        self._provider = provider
        self._cache = cache
        self._validator = validator

    def get_market_data(self, request: MarketRequest) -> MarketResult:
        """Liefert Marktdaten für die Anfrage inkl. Cache und Validierung.

        Ablauf: Bei erlaubtem Cache zuerst dort nachsehen. Andernfalls (oder
        bei Fehltreffer) über den Provider laden, die Ergebnisse validieren und
        – sofern brauchbar – im Cache ablegen.

        Args:
            request: Die Marktdatenanfrage.

        Returns:
            Ein :class:`MarketResult`; Validierungsfehler werden in
            ``result.errors`` und ``result.metadata['validation']`` ergänzt.
        """
        cache_key = request.cache_key()

        if request.use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                _logger.debug("Cache-Treffer für %s", cache_key)
                cached.metadata["cache_hit"] = True
                return cached

        _logger.debug("Lade Daten über Provider '%s' für %s", self._provider.name, cache_key)
        result = self._provider.fetch(request)
        self._validate_result(result, request)
        result.metadata["cache_hit"] = False

        if request.use_cache and result.status in (MarketStatus.OK, MarketStatus.PARTIAL):
            category = CacheCategory.INTRADAY if request.is_intraday else CacheCategory.HISTORICAL
            self._cache.set(cache_key, result, category)

        return result

    def _validate_result(self, result: MarketResult, request: MarketRequest) -> None:
        """Validiert alle Symbol-Frames und ergänzt Befunde am Ergebnis."""
        validation_summary: dict[str, list[str]] = {}
        for symbol, frame in result.data.items():
            report = self._validator.validate_frame(symbol, frame, request.interval)
            if report.issues:
                messages = [f"{issue.severity.value}: {issue.message}" for issue in report.issues]
                validation_summary[symbol] = messages
            for issue_error in report.errors:
                result.add_error(f"{symbol}: {issue_error.message}")
        if validation_summary:
            result.metadata["validation"] = validation_summary
