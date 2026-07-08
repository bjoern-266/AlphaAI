"""Wiederverwendbare Hilfsfunktionen für die Data-Layer-Tests."""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from core.config import Settings
from data.market_data_engine import MarketDataEngine
from data.market_result import OHLCV_COLUMNS
from providers.yahoo_provider import DownloadFn, YahooProvider
from repositories.repository_factory import build_repository


def make_ohlcv(rows: int = 5, start: str = "2024-01-01", freq: str = "D") -> pd.DataFrame:
    """Erzeugt einen gültigen OHLCV-DataFrame im kanonischen Schema.

    Args:
        rows: Anzahl der Zeilen (Kerzen).
        start: Startdatum des Zeitindex.
        freq: Frequenz des Zeitindex (pandas-Offset-Alias).

    Returns:
        DataFrame mit den kanonischen OHLCV-Spalten und DatetimeIndex.
    """
    index = pd.date_range(start=start, periods=rows, freq=freq)
    base = range(1, rows + 1)
    frame = pd.DataFrame(
        {
            "open": [10.0 + i for i in base],
            "high": [11.0 + i for i in base],
            "low": [9.0 + i for i in base],
            "close": [10.5 + i for i in base],
            "adj_close": [10.5 + i for i in base],
            "volume": [1000 + i for i in base],
        },
        index=index,
    )
    return frame[list(OHLCV_COLUMNS)]


def make_yahoo_raw(rows: int = 5, start: str = "2024-01-01") -> pd.DataFrame:
    """Erzeugt einen Roh-DataFrame im yfinance-Format (Spalten wie yfinance)."""
    index = pd.date_range(start=start, periods=rows, freq="D")
    base = range(1, rows + 1)
    return pd.DataFrame(
        {
            "Open": [10.0 + i for i in base],
            "High": [11.0 + i for i in base],
            "Low": [9.0 + i for i in base],
            "Close": [10.5 + i for i in base],
            "Adj Close": [10.4 + i for i in base],
            "Volume": [1000 + i for i in base],
        },
        index=index,
    )


class FakeClock:
    """Kontrollierbare Uhr für zeitabhängige Tests."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        """Rückt die Uhr um die angegebene Sekundenzahl vor."""
        self._now += seconds


def make_price_frame(
    closes: list[float],
    highs: list[float] | None = None,
    lows: list[float] | None = None,
    opens: list[float] | None = None,
    volume: list[float] | None = None,
    start: str = "2023-01-01",
    freq: str = "D",
) -> pd.DataFrame:
    """Baut einen OHLCV-DataFrame im kanonischen Schema aus Schlusskursen.

    High/Low/Open/Volume werden – falls nicht angegeben – aus den Schlusskursen
    abgeleitet (High = Close + 1, Low = Close - 1, Open = Close, Volume = 1000).
    """
    n = len(closes)
    index = pd.date_range(start=start, periods=n, freq=freq)
    return pd.DataFrame(
        {
            "open": [float(v) for v in (opens if opens is not None else closes)],
            "high": [float(v) for v in (highs if highs is not None else [c + 1 for c in closes])],
            "low": [float(v) for v in (lows if lows is not None else [c - 1 for c in closes])],
            "close": [float(v) for v in closes],
            "adj_close": [float(v) for v in closes],
            "volume": [float(v) for v in (volume if volume is not None else [1000.0] * n)],
        },
        index=index,
    )


def make_engine(
    download_fn: DownloadFn,
    settings: Settings,
    clock: Callable[[], float],
    universe_resolver: Callable | None = None,
) -> MarketDataEngine:
    """Baut einen echten, aber netzwerkfreien MarketDataEngine.

    Nutzt den realen Repository-/Cache-/Validator-Stack mit einem
    YahooProvider, dessen Download-Funktion injiziert ist.
    """
    provider = YahooProvider(download_fn=download_fn)
    repository = build_repository(settings, provider=provider, clock=clock)
    return MarketDataEngine(repository, settings, universe_resolver=universe_resolver)
