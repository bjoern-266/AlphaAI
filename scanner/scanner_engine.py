"""Scanner-Engine – Einstiegspunkt eines Scans.

Die :class:`ScannerEngine` kennt **ausschließlich** die :class:`ScanPipeline`.
Sie kennt keine Provider, keine Repositories und keine Indikatoren. Ihre
Aufgabe ist es, einen Scan anzustoßen und den Ablauf zu protokollieren
(Start, Ende, Universum, Anzahl Symbole, Laufzeit, Warnungen, Fehler).
"""

from __future__ import annotations

from core.logging_config import get_logger
from scanner.scan_pipeline import ScanPipeline
from scanner.scan_request import ScanRequest
from scanner.scan_result import ScanReport

_logger = get_logger(__name__)


class ScannerEngine:
    """Stößt Scans an und protokolliert den Ablauf.

    Args:
        pipeline: Die zu verwendende Scan-Pipeline.
    """

    def __init__(self, pipeline: ScanPipeline) -> None:
        self._pipeline = pipeline

    def scan(self, request: ScanRequest) -> ScanReport:
        """Führt einen Scan aus und protokolliert Start und Ende.

        Args:
            request: Die auszuführende Scan-Anfrage.

        Returns:
            Das :class:`ScanReport` der Pipeline.
        """
        _logger.info(
            "Scanner Start | Markt=%s | Universum=%s",
            request.market,
            request.universe or "(explizite Symbole)",
        )

        report = self._pipeline.run(request)

        statistics = report.statistics
        runtime = statistics.runtime_seconds if statistics else 0.0
        warnings = len(report.no_data_results)
        errors = len(report.error_results)

        if warnings:
            _logger.warning("Scan mit %d Symbol(en) ohne Daten abgeschlossen.", warnings)
        if errors:
            _logger.error("Scan mit %d fehlerhaften Symbol(en) abgeschlossen.", errors)

        _logger.info(
            "Scanner Ende | Symbole=%d | Laufzeit=%.3fs | Provider=%s | "
            "Cache-Treffer=%s | Warnungen=%d | Fehler=%d",
            report.symbol_count,
            runtime,
            statistics.provider if statistics else "unbekannt",
            statistics.cache_hits if statistics else 0,
            warnings,
            errors,
        )
        return report
