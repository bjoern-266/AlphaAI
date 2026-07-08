"""Validierung von Marktdaten.

Der :class:`MarketDataValidator` prüft geladene Kursdaten auf typische
Qualitätsprobleme, bevor sie weiterverarbeitet werden. Er arbeitet
zerstörungsfrei: Er verändert die Daten nicht, sondern meldet Befunde als
:class:`ValidationReport` zurück. Die aufrufende Schicht entscheidet, wie mit
Fehlern und Warnungen umgegangen wird.

Geprüft werden:

- fehlende Werte (NaN),
- negative oder null Preise,
- doppelte Zeitstempel,
- fehlende Kerzen (Lücken) – als Warnung, siehe Hinweis unten,
- ungültige Symbole (Formatprüfung).

Hinweis zu fehlenden Kerzen: Eine vollständig kalendergenaue Prüfung
erfordert Handelskalender inkl. Feiertagen. Diese pragmatische Prüfung meldet
Lücken relativ zum erwarteten Intervall und ist bewusst als Warnung (nicht als
Fehler) eingestuft. Die exakte Kalenderprüfung ist einem späteren Sprint
vorbehalten.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

import pandas as pd

from data.market_result import COL_VOLUME, OHLCV_COLUMNS

# Erlaubte Zeichen für ein Symbol: Buchstaben, Ziffern und die in der
# yfinance-Notation üblichen Sonderzeichen (Punkt, Bindestrich, Zirkumflex,
# Gleichheitszeichen für Devisen/Futures).
_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.\-^=]{1,20}$")

# Preisspalten (Volumen darf 0 sein, Preise nicht).
_PRICE_COLUMNS: tuple[str, ...] = tuple(c for c in OHLCV_COLUMNS if c != COL_VOLUME)

# Erwartete Zeitdifferenz je Intervall für die Lückenerkennung. Nur Intervalle
# mit fester Länge sind enthalten; für andere wird die Lückenprüfung
# übersprungen.
_INTERVAL_TIMEDELTAS: dict[str, pd.Timedelta] = {
    "1m": pd.Timedelta(minutes=1),
    "2m": pd.Timedelta(minutes=2),
    "5m": pd.Timedelta(minutes=5),
    "15m": pd.Timedelta(minutes=15),
    "30m": pd.Timedelta(minutes=30),
    "60m": pd.Timedelta(minutes=60),
    "90m": pd.Timedelta(minutes=90),
    "1h": pd.Timedelta(hours=1),
    "1d": pd.Timedelta(days=1),
}


class Severity(Enum):
    """Schweregrad eines Validierungsbefunds."""

    ERROR = "error"
    WARNING = "warning"


class IssueCode(Enum):
    """Art eines Validierungsbefunds."""

    EMPTY = "empty"
    MISSING_COLUMN = "missing_column"
    NAN = "nan"
    NEGATIVE_PRICE = "negative_price"
    DUPLICATE_TIMESTAMP = "duplicate_timestamp"
    UNSORTED_TIMESTAMP = "unsorted_timestamp"
    MISSING_CANDLE = "missing_candle"
    INVALID_SYMBOL = "invalid_symbol"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Einzelner Validierungsbefund.

    Attributes:
        code: Art des Befunds.
        severity: Schweregrad (Fehler oder Warnung).
        message: Menschenlesbare Beschreibung.
    """

    code: IssueCode
    severity: Severity
    message: str


@dataclass(slots=True)
class ValidationReport:
    """Sammlung der Befunde für ein Symbol.

    Attributes:
        symbol: Das geprüfte Symbol.
        issues: Liste der gefundenen Probleme.
    """

    symbol: str
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        """Gibt nur die als Fehler eingestuften Befunde zurück."""
        return [issue for issue in self.issues if issue.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Gibt nur die als Warnung eingestuften Befunde zurück."""
        return [issue for issue in self.issues if issue.severity is Severity.WARNING]

    @property
    def is_valid(self) -> bool:
        """Gibt zurück, ob keine Fehler (nur ggf. Warnungen) vorliegen."""
        return not self.errors


class MarketDataValidator:
    """Prüft Symbole und Kursdaten auf Qualitätsprobleme.

    Args:
        gap_tolerance: Faktor, ab dem eine Zeitlücke als fehlende Kerze gilt.
            Eine Lücke wird gemeldet, wenn der Abstand zweier Zeitstempel das
            ``gap_tolerance``-Fache des erwarteten Intervalls überschreitet.
            Der Standardwert 1.5 toleriert kleine Schwankungen.
    """

    def __init__(self, gap_tolerance: float = 1.5) -> None:
        self._gap_tolerance = gap_tolerance

    def validate_symbol(self, symbol: str) -> ValidationIssue | None:
        """Prüft das Format eines Symbols.

        Args:
            symbol: Zu prüfendes Symbol.

        Returns:
            Ein :class:`ValidationIssue`, falls das Symbol ungültig ist, sonst
            ``None``.
        """
        if not _SYMBOL_PATTERN.match(symbol.strip().upper()):
            return ValidationIssue(
                code=IssueCode.INVALID_SYMBOL,
                severity=Severity.ERROR,
                message=f"Ungültiges Symbolformat: '{symbol}'.",
            )
        return None

    def validate_frame(self, symbol: str, frame: pd.DataFrame, interval: str) -> ValidationReport:
        """Prüft einen einzelnen Kurs-DataFrame.

        Args:
            symbol: Symbol, zu dem der DataFrame gehört.
            frame: Kursdaten mit kanonischem OHLCV-Schema.
            interval: Kerzenintervall (für die Lückenerkennung).

        Returns:
            Ein :class:`ValidationReport` mit allen Befunden.
        """
        report = ValidationReport(symbol=symbol)

        symbol_issue = self.validate_symbol(symbol)
        if symbol_issue is not None:
            report.issues.append(symbol_issue)

        if frame is None or frame.empty:
            report.issues.append(
                ValidationIssue(
                    code=IssueCode.EMPTY,
                    severity=Severity.ERROR,
                    message=f"Keine Daten für Symbol '{symbol}'.",
                )
            )
            return report

        self._check_columns(frame, report)
        self._check_nan(frame, report)
        self._check_negative_prices(frame, report)
        self._check_timestamps(frame, report)
        self._check_missing_candles(frame, interval, report)

        return report

    def _check_columns(self, frame: pd.DataFrame, report: ValidationReport) -> None:
        """Meldet fehlende Pflichtspalten."""
        missing = [column for column in OHLCV_COLUMNS if column not in frame.columns]
        for column in missing:
            report.issues.append(
                ValidationIssue(
                    code=IssueCode.MISSING_COLUMN,
                    severity=Severity.ERROR,
                    message=f"Fehlende Spalte '{column}'.",
                )
            )

    def _check_nan(self, frame: pd.DataFrame, report: ValidationReport) -> None:
        """Meldet Spalten mit fehlenden Werten (NaN)."""
        for column in OHLCV_COLUMNS:
            if column in frame.columns:
                nan_count = int(frame[column].isna().sum())
                if nan_count > 0:
                    report.issues.append(
                        ValidationIssue(
                            code=IssueCode.NAN,
                            severity=Severity.ERROR,
                            message=f"{nan_count} fehlende Werte (NaN) in Spalte '{column}'.",
                        )
                    )

    def _check_negative_prices(self, frame: pd.DataFrame, report: ValidationReport) -> None:
        """Meldet negative oder null Preise sowie negatives Volumen."""
        for column in _PRICE_COLUMNS:
            if column in frame.columns:
                invalid = int((frame[column] <= 0).sum())
                if invalid > 0:
                    report.issues.append(
                        ValidationIssue(
                            code=IssueCode.NEGATIVE_PRICE,
                            severity=Severity.ERROR,
                            message=f"{invalid} nicht-positive Preise in Spalte '{column}'.",
                        )
                    )
        if COL_VOLUME in frame.columns:
            negative_volume = int((frame[COL_VOLUME] < 0).sum())
            if negative_volume > 0:
                report.issues.append(
                    ValidationIssue(
                        code=IssueCode.NEGATIVE_PRICE,
                        severity=Severity.ERROR,
                        message=f"{negative_volume} negative Volumenwerte.",
                    )
                )

    def _check_timestamps(self, frame: pd.DataFrame, report: ValidationReport) -> None:
        """Meldet doppelte oder unsortierte Zeitstempel im Index."""
        index = frame.index
        duplicates = int(index.duplicated().sum())
        if duplicates > 0:
            report.issues.append(
                ValidationIssue(
                    code=IssueCode.DUPLICATE_TIMESTAMP,
                    severity=Severity.ERROR,
                    message=f"{duplicates} doppelte Zeitstempel.",
                )
            )
        if not index.is_monotonic_increasing:
            report.issues.append(
                ValidationIssue(
                    code=IssueCode.UNSORTED_TIMESTAMP,
                    severity=Severity.ERROR,
                    message="Zeitstempel sind nicht aufsteigend sortiert.",
                )
            )

    def _check_missing_candles(
        self, frame: pd.DataFrame, interval: str, report: ValidationReport
    ) -> None:
        """Meldet mögliche fehlende Kerzen anhand von Zeitlücken (Warnung)."""
        expected = _INTERVAL_TIMEDELTAS.get(interval)
        if expected is None or len(frame.index) < 2:
            return
        if not isinstance(frame.index, pd.DatetimeIndex):
            return

        deltas = frame.index.to_series().diff().dropna()
        threshold = expected * self._gap_tolerance
        gaps = int((deltas > threshold).sum())
        if gaps > 0:
            report.issues.append(
                ValidationIssue(
                    code=IssueCode.MISSING_CANDLE,
                    severity=Severity.WARNING,
                    message=(
                        f"{gaps} mögliche Lücke(n) im Zeitraster erkannt "
                        f"(Intervall '{interval}'). Kann durch Wochenenden/Feiertage "
                        f"verursacht sein."
                    ),
                )
            )
