"""Yahoo-Finance-Provider auf Basis von yfinance.

Dieser Provider ist die erste (und aktuell einzige) implementierte Datenquelle.
Er lädt Kursdaten symbolweise und normalisiert sie auf das kanonische
OHLCV-Schema von :class:`MarketResult`.

Testbarkeit: Der eigentliche Netzwerkzugriff steckt hinter einer injizierbaren
Download-Funktion (``download_fn``). In Tests wird dafür eine Attrappe
übergeben, sodass keine echte Netzwerkverbindung nötig ist (Dependency
Injection). Nur die Standardimplementierung importiert ``yfinance`` – und zwar
verzögert, damit das Modul auch ohne installiertes yfinance importierbar bleibt.
"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from core.logging_config import get_logger
from data.market_request import MarketRequest
from data.market_result import (
    COL_ADJ_CLOSE,
    COL_CLOSE,
    COL_HIGH,
    COL_LOW,
    COL_OPEN,
    COL_VOLUME,
    OHLCV_COLUMNS,
    MarketResult,
    MarketStatus,
)
from providers.base_provider import BaseProvider

# Signatur der Download-Funktion: (symbol, timeframe, interval) -> Roh-DataFrame
# im yfinance-Format (Spalten Open/High/Low/Close/Adj Close/Volume).
DownloadFn = Callable[[str, str, str], pd.DataFrame]

_logger = get_logger(__name__)

# Zuordnung normalisierter Roh-Spaltennamen -> kanonische Spalten.
_COLUMN_MAP: dict[str, str] = {
    "open": COL_OPEN,
    "high": COL_HIGH,
    "low": COL_LOW,
    "close": COL_CLOSE,
    "adjclose": COL_ADJ_CLOSE,
    "volume": COL_VOLUME,
}


def _default_download(symbol: str, timeframe: str, interval: str) -> pd.DataFrame:
    """Standard-Download über yfinance (verzögerter Import).

    Args:
        symbol: Einzelnes Symbol.
        timeframe: Zeitraum/Rückschau (yfinance ``period``).
        interval: Kerzenintervall (yfinance ``interval``).

    Returns:
        Roh-DataFrame von yfinance.
    """
    import yfinance as yf

    return yf.download(
        tickers=symbol,
        period=timeframe,
        interval=interval,
        auto_adjust=False,
        progress=False,
    )


def _normalize_column(name: object) -> str:
    """Normalisiert einen Roh-Spaltennamen (klein, ohne Leerzeichen)."""
    return str(name).strip().lower().replace(" ", "")


class YahooProvider(BaseProvider):
    """Provider für Yahoo Finance.

    Args:
        download_fn: Optionale Download-Funktion. Standardmäßig wird yfinance
            verwendet; für Tests kann eine Attrappe injiziert werden.
    """

    name = "yahoo"

    def __init__(self, download_fn: DownloadFn | None = None) -> None:
        self._download = download_fn or _default_download

    def fetch(self, request: MarketRequest) -> MarketResult:
        """Lädt und normalisiert die Kursdaten für alle Symbole der Anfrage."""
        frames: dict[str, pd.DataFrame] = {}
        errors: list[str] = []
        # Echte Abruf-Ausnahmen werden getrennt von "keine Daten" gezählt:
        # Ausnahmen führen zu ERROR, leere Antworten lediglich zu EMPTY/PARTIAL.
        has_failures = False

        for symbol in request.symbols:
            try:
                raw = self._download(symbol, request.timeframe, request.interval)
            except Exception as error:  # Fehler der Datenquelle in Ergebnis überführen.
                _logger.warning("Yahoo-Abruf für %s fehlgeschlagen: %s", symbol, error)
                errors.append(f"{symbol}: Abruf fehlgeschlagen ({error}).")
                has_failures = True
                continue

            normalized = self._normalize_frame(raw)
            if normalized.empty:
                errors.append(f"{symbol}: Keine Daten erhalten.")
                continue
            frames[symbol] = normalized

        metadata = {
            "timeframe": request.timeframe,
            "interval": request.interval,
            "market": request.market,
            "requested_symbols": len(request.symbols),
            "returned_symbols": len(frames),
        }
        status = self._determine_status(len(request.symbols), len(frames), has_failures)
        return MarketResult(
            provider=self.name,
            status=status,
            data=frames,
            metadata=metadata,
            errors=errors,
        )

    @staticmethod
    def _determine_status(requested: int, returned: int, has_failures: bool) -> MarketStatus:
        """Leitet den Ergebnisstatus aus den Zählwerten ab.

        Args:
            requested: Anzahl angeforderter Symbole.
            returned: Anzahl erfolgreich geladener Symbole.
            has_failures: Ob mindestens ein Abruf mit einer Ausnahme scheiterte.
        """
        if returned == 0:
            return MarketStatus.ERROR if has_failures else MarketStatus.EMPTY
        if returned < requested or has_failures:
            return MarketStatus.PARTIAL
        return MarketStatus.OK

    def _normalize_frame(self, raw: pd.DataFrame) -> pd.DataFrame:
        """Überführt einen yfinance-Roh-DataFrame ins kanonische OHLCV-Schema.

        Args:
            raw: Roh-DataFrame von yfinance (ggf. mit MultiIndex-Spalten).

        Returns:
            DataFrame mit den Spalten aus :data:`OHLCV_COLUMNS` und
            aufsteigend sortiertem :class:`~pandas.DatetimeIndex`. Bei leerer
            Eingabe wird ein leerer DataFrame mit korrektem Schema geliefert.
        """
        empty = pd.DataFrame(columns=list(OHLCV_COLUMNS))
        if raw is None or raw.empty:
            return empty

        source = raw.copy()
        # MultiIndex-Spalten (mehrere Ticker) auf die Feldebene reduzieren.
        if isinstance(source.columns, pd.MultiIndex):
            source.columns = source.columns.get_level_values(0)

        lookup = {_normalize_column(col): col for col in source.columns}
        result = pd.DataFrame(index=source.index)
        for raw_key, canonical in _COLUMN_MAP.items():
            if raw_key in lookup:
                result[canonical] = source[lookup[raw_key]]

        # Fehlt 'Adj Close' (z. B. bei bereits bereinigten Daten), Close nutzen.
        if COL_ADJ_CLOSE not in result.columns and COL_CLOSE in result.columns:
            result[COL_ADJ_CLOSE] = result[COL_CLOSE]

        if result.empty or COL_CLOSE not in result.columns:
            return empty

        result = result.reindex(columns=list(OHLCV_COLUMNS))
        result.index = pd.to_datetime(result.index)
        result = result.sort_index()
        return result
