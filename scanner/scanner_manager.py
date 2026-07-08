"""Scanner-Manager – Vorbereitung für Mehrfach-Scans.

Der :class:`ScannerManager` koordiniert mehrere Scans über verschiedene
Märkte, Universen und Zeiträume hinweg. Aktuell erfolgt die Ausführung
**sequenziell** (keine Parallelisierung); die Struktur ist jedoch so angelegt,
dass eine spätere Parallelisierung (siehe ``max_workers`` in der Anfrage) ohne
Umbau der aufrufenden Seite möglich ist.
"""

from __future__ import annotations

from collections.abc import Iterable

from core.config import Settings
from core.logging_config import get_logger
from scanner.scan_request import ScanRequest, build_scan_request
from scanner.scan_result import ScanReport
from scanner.scanner_engine import ScannerEngine

_logger = get_logger(__name__)


class ScannerManager:
    """Führt mehrere Scans nacheinander aus.

    Args:
        engine: Die zu verwendende Scanner-Engine.
        settings: Projektkonfiguration (für Standardwerte beim Anfragenbau).
    """

    def __init__(self, engine: ScannerEngine, settings: Settings) -> None:
        self._engine = engine
        self._settings = settings

    def scan_all(self, requests: Iterable[ScanRequest]) -> list[ScanReport]:
        """Führt alle übergebenen Anfragen sequenziell aus.

        Args:
            requests: Die auszuführenden Scan-Anfragen.

        Returns:
            Ein :class:`ScanReport` je Anfrage, in Eingabereihenfolge.
        """
        request_list = list(requests)
        _logger.info("ScannerManager startet %d Scan(s) (sequenziell).", len(request_list))
        return [self._engine.scan(request) for request in request_list]

    def build_requests(
        self,
        universes: Iterable[str],
        timeframes: Iterable[str],
        interval: str | None = None,
        use_cache: bool = True,
    ) -> list[ScanRequest]:
        """Erzeugt Anfragen für jede Kombination aus Universum und Zeitraum.

        Diese Vorbereitung ermöglicht Scans über mehrere Märkte/Universen und
        mehrere Zeiträume. Standardwerte (Features, Worker) stammen aus der
        Konfiguration.

        Args:
            universes: Universumsschlüssel (jeweils auch als Marktname genutzt).
            timeframes: Zu scannende Zeiträume/Rückschauen.
            interval: Kerzenintervall (``None`` = Standard aus Konfiguration).
            use_cache: Ob der Cache verwendet werden darf.

        Returns:
            Liste der erzeugten :class:`ScanRequest`-Objekte.
        """
        timeframe_list = list(timeframes)
        requests: list[ScanRequest] = []
        for universe in universes:
            for timeframe in timeframe_list:
                requests.append(
                    build_scan_request(
                        settings=self._settings,
                        market=universe,
                        universe=universe,
                        timeframe=timeframe,
                        interval=interval,
                        use_cache=use_cache,
                    )
                )
        return requests
