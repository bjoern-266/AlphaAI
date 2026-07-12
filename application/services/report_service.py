"""Lesedienst für gespeicherte Reports.

Der :class:`ReportService` ist die einzige Stelle, über die die API auf die
persistierten Reports zugreift. Er **liest** ausschließlich: er holt den
zuletzt gespeicherten Report einer Art aus dem :class:`ReportStore` und wählt
bei Bedarf Teilmengen aus (z. B. eine einzelne Aktie, die Top-N-Chancen). Es
findet **keine** Berechnung, Bewertung oder Ableitung statt.

Fehlt ein Report (noch kein erfolgreicher Scan), wird ein
:class:`ServiceUnavailableError` ausgelöst – der Dienst bleibt am Leben, die
Anfrage kann aber (noch) nicht bedient werden. Wird ein konkreter Ticker nicht
gefunden, folgt ein :class:`ReportNotFoundError`.
"""

from __future__ import annotations

from typing import Any

from application.exceptions import (
    InvalidRequestError,
    ReportNotFoundError,
    ServiceUnavailableError,
)
from application.repositories import ReportStore
from models.application import ReportKind, StoredReport


class ReportService:
    """Liest gespeicherte Reports und bereitet Teilmengen für die API auf.

    Args:
        store: Der dauerhafte Report-Speicher.
    """

    def __init__(self, store: ReportStore) -> None:
        self._store = store

    # ------------------------------------------------------------------ #
    # Grundlegender Zugriff
    # ------------------------------------------------------------------ #
    def stored(self, kind: ReportKind | str) -> StoredReport:
        """Gibt den zuletzt gespeicherten Report einer Art zurück.

        Raises:
            ServiceUnavailableError: Wenn (noch) kein Report dieser Art existiert.
        """
        key = kind.value if isinstance(kind, ReportKind) else str(kind)
        report = self._store.latest(key)
        if report is None:
            raise ServiceUnavailableError(
                f"Für '{key}' liegt noch kein gespeicherter Report vor.",
                detail={"kind": key},
            )
        return report

    def payload(self, kind: ReportKind | str) -> dict[str, Any]:
        """Gibt die JSON-Nutzlast des zuletzt gespeicherten Reports zurück."""
        return self.stored(kind).payload

    def has(self, kind: ReportKind | str) -> bool:
        """``True``, wenn mindestens ein Report dieser Art gespeichert ist."""
        key = kind.value if isinstance(kind, ReportKind) else str(kind)
        return self._store.latest(key) is not None

    # ------------------------------------------------------------------ #
    # Operations / System
    # ------------------------------------------------------------------ #
    def operations(self) -> dict[str, Any]:
        """Gibt den vollständigen Operations-Report zurück."""
        return self.payload(ReportKind.OPERATIONS)

    def scheduler(self) -> dict[str, Any]:
        """Gibt die Scheduler-relevanten Felder des Operations-Reports zurück."""
        report = self.payload(ReportKind.OPERATIONS)
        return {
            "as_of": report.get("as_of"),
            "next_scan_at": report.get("next_scan_at"),
            "next_scan_job": report.get("next_scan_job"),
            "running_job": report.get("running_job"),
            "last_successful_scan_at": report.get("last_successful_scan_at"),
            "scan_count": report.get("scan_count"),
            "error_count": report.get("error_count"),
            "average_runtime": report.get("average_runtime"),
            "system_state": report.get("system_state"),
            "job_history": report.get("job_history", []),
        }

    def markets(self) -> list[dict[str, Any]]:
        """Gibt die Marktzustände aus dem Operations-Report zurück."""
        clock = self.payload(ReportKind.OPERATIONS).get("market_clock") or {}
        markets = clock.get("markets")
        return list(markets) if isinstance(markets, list) else []

    def market_status(self) -> dict[str, Any]:
        """Gibt die zusammengefasste Marktuhr (offen/geschlossen/Nächste) zurück."""
        report = self.payload(ReportKind.OPERATIONS)
        clock = report.get("market_clock") or {}
        return {
            "as_of": clock.get("as_of", report.get("as_of")),
            "current_session": report.get("current_session"),
            "open_markets": clock.get("open_markets", []),
            "next_open_market": clock.get("next_open_market"),
            "next_open_at": clock.get("next_open_at"),
            "markets": clock.get("markets", []),
        }

    # ------------------------------------------------------------------ #
    # Chancen (Market Intelligence)
    # ------------------------------------------------------------------ #
    def opportunities(self) -> dict[str, Any]:
        """Gibt den vollständigen Opportunity-Report zurück."""
        return self.payload(ReportKind.OPPORTUNITIES)

    def top_opportunities(self, limit: int = 10) -> list[dict[str, Any]]:
        """Gibt die besten ``limit`` Chancen (nach Ranking) zurück.

        Raises:
            InvalidRequestError: Wenn ``limit`` kein positiver Wert ist.
        """
        bound = _positive_limit(limit)
        items = self.opportunities().get("opportunities")
        rows = list(items) if isinstance(items, list) else []
        return rows[:bound]

    def opportunity(self, ticker: str) -> dict[str, Any]:
        """Gibt die Chance zu einem Ticker zurück (Groß-/Kleinschreibung egal).

        Raises:
            InvalidRequestError: Wenn ``ticker`` leer ist.
            ReportNotFoundError: Wenn der Ticker nicht im Report enthalten ist.
        """
        key = _clean_ticker(ticker)
        items = self.opportunities().get("opportunities")
        row = _find_by_ticker(items, key)
        if row is None:
            raise ReportNotFoundError(
                f"Keine Chance für Ticker '{ticker}' gefunden.", detail={"ticker": ticker}
            )
        return row

    # ------------------------------------------------------------------ #
    # Market Discovery
    # ------------------------------------------------------------------ #
    def discovery(self) -> dict[str, Any]:
        """Gibt den vollständigen Discovery-Report zurück."""
        return self.payload(ReportKind.DISCOVERY)

    # ------------------------------------------------------------------ #
    # Empfehlungen
    # ------------------------------------------------------------------ #
    def recommendations(self) -> dict[str, Any]:
        """Gibt den vollständigen Recommendation-Report zurück."""
        return self.payload(ReportKind.RECOMMENDATIONS)

    def recommendation(self, ticker: str) -> dict[str, Any]:
        """Gibt die Empfehlung zu einem Ticker zurück.

        Die Empfehlung wird aus den bereits vorhandenen Chancen-Reports gelesen
        (Opportunity- bzw. Discovery-Report enthalten je Ticker eine Empfehlung).
        Es wird **nichts** neu berechnet.

        Raises:
            InvalidRequestError: Wenn ``ticker`` leer ist.
            ReportNotFoundError: Wenn zu dem Ticker keine Empfehlung vorliegt.
        """
        key = _clean_ticker(ticker)
        for kind in (ReportKind.OPPORTUNITIES, ReportKind.DISCOVERY):
            if not self.has(kind):
                continue
            row = _find_by_ticker(self.payload(kind).get("opportunities"), key)
            if row is not None:
                return row
        raise ReportNotFoundError(
            f"Keine Empfehlung für Ticker '{ticker}' gefunden.", detail={"ticker": ticker}
        )

    # ------------------------------------------------------------------ #
    # Analytics
    # ------------------------------------------------------------------ #
    def analytics(self) -> dict[str, Any]:
        """Gibt den vollständigen Analytics-Report zurück."""
        return self.payload(ReportKind.ANALYTICS)

    def backtesting(self) -> dict[str, Any]:
        """Gibt den vollständigen Backtesting-Report zurück."""
        return self.payload(ReportKind.BACKTESTING)

    def paper_trading(self) -> dict[str, Any]:
        """Gibt den vollständigen Paper-Trading-Report zurück."""
        return self.payload(ReportKind.PAPER_TRADING)

    # ------------------------------------------------------------------ #
    # Dashboard (zusammengesetzter Schnappschuss aller Reports)
    # ------------------------------------------------------------------ #
    def dashboard(self) -> dict[str, Any]:
        """Bündelt die zuletzt gespeicherten Reports zu einem Dashboard-Schnappschuss.

        Es werden nur vorhandene Reports übernommen; fehlende Arten bleiben
        ``None``. Es findet keine Berechnung statt – reine Zusammenstellung.

        Raises:
            ServiceUnavailableError: Wenn noch **kein** Report gespeichert ist.
        """
        bundle: dict[str, Any] = {}
        available = False
        for kind in ReportKind:
            if kind is ReportKind.DASHBOARD:
                continue
            stored = self._store.latest(kind.value)
            bundle[kind.value] = stored.payload if stored is not None else None
            available = available or stored is not None
        if not available:
            raise ServiceUnavailableError(
                "Es liegt noch kein gespeicherter Report für das Dashboard vor."
            )
        return bundle


# --------------------------------------------------------------------------- #
# Hilfsfunktionen (rein, ohne Fachlogik)
# --------------------------------------------------------------------------- #


def _clean_ticker(ticker: str) -> str:
    """Normalisiert einen Ticker (getrimmt, Großbuchstaben).

    Raises:
        InvalidRequestError: Wenn der Ticker leer ist.
    """
    key = (ticker or "").strip().upper()
    if not key:
        raise InvalidRequestError("Es wurde kein Ticker angegeben.", detail={"ticker": ticker})
    return key


def _positive_limit(limit: int) -> int:
    """Prüft und liefert ein positives Limit.

    Raises:
        InvalidRequestError: Wenn ``limit`` nicht in einen positiven Wert passt.
    """
    try:
        value = int(limit)
    except (TypeError, ValueError) as error:
        raise InvalidRequestError(
            "Der Parameter 'limit' muss eine ganze Zahl sein.", detail={"limit": limit}
        ) from error
    if value < 1:
        raise InvalidRequestError(
            "Der Parameter 'limit' muss mindestens 1 sein.", detail={"limit": limit}
        )
    return value


def _find_by_ticker(items: Any, ticker: str) -> dict[str, Any] | None:
    """Sucht in einer Liste von Dicts den ersten Eintrag mit passendem Ticker."""
    if not isinstance(items, list):
        return None
    for row in items:
        if isinstance(row, dict) and str(row.get("ticker", "")).strip().upper() == ticker:
            return row
    return None


__all__ = ["ReportService"]
