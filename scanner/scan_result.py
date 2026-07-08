"""Ergebnisobjekte eines Scans.

:class:`ScanResult` hält das Ergebnis für **ein** Symbol. Die Felder für die
spätere Analyse (Indikatoren, Muster, Score, Risiko, Empfehlung) sind bereits
vorhanden, aber im Scanner Core bewusst leer – sie werden in späteren Sprints
befüllt.

:class:`ScanReport` bündelt alle Einzelergebnisse eines Laufs samt Statistik
und ursprünglicher Anfrage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd

from scanner.scan_request import ScanRequest
from scanner.scan_statistics import ScanStatistics


class ScanStatus(Enum):
    """Statuscode eines Einzelergebnisses.

    Attributes:
        OK: Marktdaten wurden erfolgreich geladen.
        NO_DATA: Keine Daten für das Symbol vorhanden.
        ERROR: Beim Laden trat ein Fehler auf.
    """

    OK = "ok"
    NO_DATA = "no_data"
    ERROR = "error"


@dataclass(slots=True)
class ScanResult:
    """Scan-Ergebnis für ein einzelnes Symbol.

    Attributes:
        ticker: Das gescannte Symbol.
        provider: Tatsächlich verwendeter Provider.
        market: Marktbezeichnung aus der Anfrage.
        timeframe: Verwendeter Zeitraum/Rückschau.
        timestamp: Zeitpunkt der Erzeugung dieses Ergebnisses.
        status: Statuscode (:class:`ScanStatus`).
        raw_market_data: Rohe Kursdaten (kanonisches OHLCV-Schema) oder ``None``.
        metadata: Zusätzliche Informationen (z. B. Intervall, Marktstatus).
        error: Fehlermeldung, falls vorhanden.
        indicators: Vorbereitet, später befüllt – Indikatorwerte.
        patterns: Vorbereitet, später befüllt – erkannte Muster.
        score: Vorbereitet, später befüllt – Bewertung.
        risk: Vorbereitet, später befüllt – Risikoangaben.
        recommendation: Vorbereitet, später befüllt – Empfehlung.
    """

    ticker: str
    provider: str
    market: str
    timeframe: str
    timestamp: datetime
    status: ScanStatus
    raw_market_data: pd.DataFrame | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    # --- Vorbereitet für spätere Sprints (im Scanner Core bewusst leer) ---
    indicators: dict[str, Any] = field(default_factory=dict)
    patterns: list[Any] = field(default_factory=list)
    score: float | None = None
    risk: dict[str, Any] | None = None
    recommendation: str | None = None

    @property
    def has_data(self) -> bool:
        """Gibt zurück, ob rohe Marktdaten vorhanden sind."""
        return self.raw_market_data is not None and not self.raw_market_data.empty

    @property
    def is_ok(self) -> bool:
        """Gibt zurück, ob der Status OK ist."""
        return self.status is ScanStatus.OK


@dataclass(slots=True)
class ScanReport:
    """Gesamtergebnis eines Scan-Laufs.

    Attributes:
        request: Die zugrunde liegende Anfrage.
        results: Einzelergebnisse je Symbol.
        statistics: Kennzahlen des Laufs.
    """

    request: ScanRequest
    results: list[ScanResult] = field(default_factory=list)
    statistics: ScanStatistics | None = None

    @property
    def ok_results(self) -> list[ScanResult]:
        """Ergebnisse mit Status OK."""
        return [r for r in self.results if r.status is ScanStatus.OK]

    @property
    def error_results(self) -> list[ScanResult]:
        """Ergebnisse mit Status ERROR."""
        return [r for r in self.results if r.status is ScanStatus.ERROR]

    @property
    def no_data_results(self) -> list[ScanResult]:
        """Ergebnisse ohne Daten (Status NO_DATA)."""
        return [r for r in self.results if r.status is ScanStatus.NO_DATA]

    @property
    def symbol_count(self) -> int:
        """Anzahl der Einzelergebnisse."""
        return len(self.results)
