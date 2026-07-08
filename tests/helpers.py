"""Wiederverwendbare Hilfsfunktionen für die Tests."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import pandas as pd

from core.config import Settings
from data.market_data_engine import MarketDataEngine
from data.market_result import OHLCV_COLUMNS
from engines.indicator_result import IndicatorResult
from engines.pattern_result import PatternReport
from indicators.base import IndicatorOutput
from patterns.base import PatternDirection, PatternResult, PatternType
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


def _one(value: float) -> pd.Series:
    """Einelementige Serie (für Test-Indikatorwerte)."""
    return pd.Series([float(value)])


def make_indicator_result(
    ema: dict[int, float] | None = None,
    rsi: float | None = None,
    atr: float | None = None,
    adx: float | None = None,
    macd: dict[str, float] | None = None,
    relative_volume: float | None = None,
    bollinger: dict[str, float] | None = None,
    valid: bool = True,
    candle_count: int = 260,
    timeframe: str = "base",
) -> IndicatorResult:
    """Baut ein IndicatorResult mit gezielt gesetzten letzten Werten (für Tests)."""
    outputs: dict[str, IndicatorOutput] = {}
    if ema is not None:
        outputs["ema"] = IndicatorOutput(
            name="ema", series={f"ema_{p}": _one(v) for p, v in ema.items()}
        )
    if rsi is not None:
        outputs["rsi"] = IndicatorOutput(name="rsi", series={"rsi_14": _one(rsi)})
    if atr is not None:
        outputs["atr"] = IndicatorOutput(name="atr", series={"atr_14": _one(atr)})
    if adx is not None:
        outputs["adx"] = IndicatorOutput(name="adx", series={"adx": _one(adx)})
    if macd is not None:
        outputs["macd"] = IndicatorOutput(name="macd", series={k: _one(v) for k, v in macd.items()})
    if relative_volume is not None:
        outputs["relative_volume"] = IndicatorOutput(
            name="relative_volume", series={"relative_volume": _one(relative_volume)}
        )
    if bollinger is not None:
        outputs["bollinger"] = IndicatorOutput(
            name="bollinger", series={k: _one(v) for k, v in bollinger.items()}
        )
    return IndicatorResult(
        outputs=outputs,
        valid=valid,
        metadata={"candle_count": candle_count, "timeframe": timeframe, "rules_version": 2},
    )


def make_pattern_result(
    name: str,
    direction: PatternDirection = PatternDirection.BULLISH,
    strength: float = 50.0,
    confidence: float = 0.6,
    price_level: float = 100.0,
    timestamp: datetime | None = None,
    fresh: bool = True,
    pattern_type: PatternType = PatternType.FAIR_VALUE_GAP,
) -> PatternResult:
    """Baut ein einzelnes PatternResult (für Tests)."""
    return PatternResult(
        name=name,
        pattern_type=pattern_type,
        direction=direction,
        strength=strength,
        confidence=confidence,
        timestamp=timestamp or datetime(2024, 1, 1, tzinfo=UTC),
        price_level=price_level,
        metadata={"fresh": fresh},
    )


def make_pattern_report(
    results: list[PatternResult] | None = None,
    valid: bool = True,
    candle_count: int = 260,
    timeframe: str = "base",
) -> PatternReport:
    """Baut ein PatternReport mit gegebenen Ergebnissen (für Tests)."""
    return PatternReport(
        results=results or [],
        valid=valid,
        metadata={"candle_count": candle_count, "timeframe": timeframe, "rules_version": 2},
    )
