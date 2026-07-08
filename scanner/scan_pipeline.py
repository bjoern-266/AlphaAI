"""Scan-Pipeline – reine Orchestrierung.

Die :class:`ScanPipeline` steuert den Ablauf eines Scans, führt aber selbst
**keine** Analyse durch. Ablauf:

1. Universum laden (falls angegeben) und mit expliziten Symbolen zusammenführen.
2. Für jedes Symbol die :class:`~data.market_data_engine.MarketDataEngine`
   aufrufen.
3. Die Marktdaten einsammeln und je Symbol ein :class:`ScanResult` erzeugen.
4. Währenddessen Statistik führen (Zeiten, Cache-Treffer, Fehler).

Die Pipeline kennt die ``MarketDataEngine`` und die Universums-Auflösung –
nicht jedoch Provider oder Repositories (diese liegen in der Data Layer).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from core.logging_config import get_logger
from data.market_data_engine import MarketDataEngine
from data.market_result import MarketResult, MarketStatus
from data.universe import Universe, get_universe
from scanner.scan_request import ScanRequest
from scanner.scan_result import ScanReport, ScanResult, ScanStatus
from scanner.scan_statistics import ScanStatistics

_logger = get_logger(__name__)

# Auflösefunktion für Universen und Zeitquelle – beide injizierbar für Tests.
UniverseResolver = Callable[[str], Universe]
NowFn = Callable[[], datetime]


def _utcnow() -> datetime:
    """Gibt die aktuelle Zeit als zeitzonenbewusste UTC-Zeit zurück."""
    return datetime.now(UTC)


class ScanPipeline:
    """Orchestriert einen Scan-Lauf (ohne jegliche Analyse).

    Args:
        engine: Marktdaten-Engine zum Laden der Kursdaten.
        universe_resolver: Auflösung eines Universumsschlüssels zu Symbolen.
        now_fn: Zeitquelle für Zeitstempel und Statistik (injizierbar).
    """

    def __init__(
        self,
        engine: MarketDataEngine,
        universe_resolver: UniverseResolver | None = None,
        now_fn: NowFn = _utcnow,
    ) -> None:
        self._engine = engine
        self._resolve_universe = universe_resolver or get_universe
        self._now = now_fn

    def run(self, request: ScanRequest) -> ScanReport:
        """Führt den Scan gemäß Anfrage aus.

        Args:
            request: Die auszuführende Scan-Anfrage.

        Returns:
            Ein :class:`ScanReport` mit Einzelergebnissen und Statistik.
        """
        statistics = ScanStatistics(provider=request.provider or "default", now_fn=self._now)
        statistics.start()

        symbols = self._resolve_symbols(request)
        _logger.debug(
            "Pipeline verarbeitet %d Symbol(e) für Markt '%s'.", len(symbols), request.market
        )

        results = [self._scan_symbol(symbol, request, statistics) for symbol in symbols]

        statistics.finish()
        return ScanReport(request=request, results=results, statistics=statistics)

    def _resolve_symbols(self, request: ScanRequest) -> list[str]:
        """Ermittelt die zu scannenden Symbole aus Universum und Anfrage.

        Symbole aus dem Universum und explizit angegebene Symbole werden
        zusammengeführt und dedupliziert (Reihenfolge bleibt erhalten).
        """
        ordered: dict[str, None] = {}
        if request.universe:
            universe = self._resolve_universe(request.universe)
            for symbol in universe.symbols:
                ordered[symbol] = None
        for symbol in request.symbols:
            ordered[symbol] = None
        return list(ordered)

    def _scan_symbol(
        self, symbol: str, request: ScanRequest, statistics: ScanStatistics
    ) -> ScanResult:
        """Lädt die Daten eines Symbols und erzeugt das zugehörige ScanResult."""
        market_result = self._engine.get_symbols(
            symbols=[symbol],
            timeframe=request.timeframe,
            interval=request.interval,
            market=request.market,
            use_cache=request.use_cache,
        )
        cache_hit = bool(market_result.metadata.get("cache_hit", False))
        status, error = self._map_status(symbol, market_result)

        statistics.provider = market_result.provider
        statistics.record_symbol(cache_hit=cache_hit, error_message=error)

        return ScanResult(
            ticker=symbol,
            provider=market_result.provider,
            market=request.market,
            timeframe=str(market_result.metadata.get("timeframe", request.timeframe or "")),
            timestamp=self._now(),
            status=status,
            raw_market_data=market_result.frame(symbol),
            metadata={
                "interval": market_result.metadata.get("interval", request.interval),
                "market_status": market_result.status.value,
                "cache_hit": cache_hit,
                "requested_features": list(request.requested_features),
            },
            error=error,
        )

    @staticmethod
    def _map_status(symbol: str, market_result: MarketResult) -> tuple[ScanStatus, str | None]:
        """Leitet den ScanStatus und eine mögliche Fehlermeldung ab."""
        if market_result.status is MarketStatus.ERROR:
            return ScanStatus.ERROR, "; ".join(market_result.errors) or "Unbekannter Fehler."
        frame = market_result.frame(symbol)
        if frame is None or frame.empty:
            message = "; ".join(market_result.errors) or "Keine Daten."
            return ScanStatus.NO_DATA, message
        return ScanStatus.OK, None
