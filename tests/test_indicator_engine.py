"""Tests für die IndicatorEngine (Orchestrierung, Validierung, Cache, Performance)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from data.market_result import MarketResult, MarketStatus
from engines.indicator_cache import IndicatorCache
from engines.indicator_engine import IndicatorEngine, load_indicator_rules
from tests.helpers import make_price_frame


def _big_frame(rows: int = 260, seed: int = 7) -> pd.DataFrame:
    """Erzeugt einen realistischen OHLCV-DataFrame mit ``rows`` Kerzen."""
    rng = np.random.default_rng(seed)
    index = pd.date_range("2022-01-01", periods=rows, freq="D")
    close = 100.0 + np.cumsum(rng.normal(0.1, 1.0, rows))
    high = close + rng.uniform(0.1, 1.0, rows)
    low = close - rng.uniform(0.1, 1.0, rows)
    return pd.DataFrame(
        {
            "open": close + rng.normal(0.0, 0.3, rows),
            "high": high,
            "low": low,
            "close": close,
            "adj_close": close,
            "volume": rng.uniform(1000.0, 5000.0, rows),
        },
        index=index,
    )


def _engine(cache: IndicatorCache | None = None) -> IndicatorEngine:
    return IndicatorEngine(load_indicator_rules(), cache=cache)


def test_engine_computes_all_named_fields() -> None:
    result = _engine().calculate(_big_frame(), symbol="TEST")
    assert result.valid is True
    for value in (
        result.ema20,
        result.ema50,
        result.ema200,
        result.rsi14,
        result.atr14,
        result.vwap,
        result.macd,
        result.relative_volume,
        result.adx,
        result.obv,
    ):
        assert value is not None
    assert result.bollinger_bands["middle"] is not None
    assert result.stochastic["percent_k"] is not None
    assert result.volume_profile is not None
    assert len(result.metadata["computed"]) == 11


def test_engine_records_calculation_time() -> None:
    result = _engine().calculate(_big_frame())
    assert result.calculation_time >= 0.0


def test_engine_too_little_history_is_invalid() -> None:
    result = _engine().calculate(make_price_frame([100.0] * 5))
    assert result.valid is False
    assert any("Zu wenig Historie" in w for w in result.warnings)


def test_engine_missing_columns_is_invalid() -> None:
    frame = pd.DataFrame({"close": [1.0, 2.0, 3.0]})
    result = _engine().calculate(frame)
    assert result.valid is False
    assert any("Pflichtspalten" in w for w in result.warnings)


def test_engine_skips_volume_indicators_without_volume() -> None:
    frame = _big_frame()
    frame["volume"] = 0.0  # kein nutzbares Volumen
    result = _engine().calculate(frame)
    assert "vwap" not in result.outputs
    assert "obv" not in result.outputs
    assert any("Fehlende Volumendaten" in w for w in result.warnings)


def test_engine_partial_ema_without_enough_history() -> None:
    # 60 Kerzen: EMA(20) real, EMA(200) mangels Historie None.
    result = _engine().calculate(_big_frame(rows=60))
    assert result.ema20 is not None
    assert result.ema200 is None


def test_engine_skips_indicator_with_insufficient_history() -> None:
    # 25 Kerzen: MACD (braucht 35) wird übersprungen und als Warnung vermerkt.
    result = _engine().calculate(_big_frame(rows=25))
    assert "macd" not in result.outputs
    assert any("Zu wenig Historie für 'macd'" in w for w in result.warnings)


def test_engine_uses_cache() -> None:
    cache = IndicatorCache()
    engine = _engine(cache=cache)
    frame = _big_frame()
    engine.calculate(frame, symbol="X")
    engine.calculate(frame, symbol="X")
    assert cache.hits == 1
    assert cache.misses == 1


def test_engine_calculate_symbol_missing_symbol() -> None:
    empty = MarketResult(provider="yahoo", status=MarketStatus.EMPTY)
    result = _engine().calculate_symbol(empty, "AAPL")
    assert result.valid is False
    assert any("Keine Marktdaten" in w for w in result.warnings)


def test_engine_calculate_all_symbols() -> None:
    data = {"AAPL": _big_frame(seed=1), "MSFT": _big_frame(seed=2)}
    market = MarketResult(provider="yahoo", status=MarketStatus.OK, data=data)
    results = _engine().calculate_all(market)
    assert set(results) == {"AAPL", "MSFT"}
    assert all(r.valid for r in results.values())


def test_engine_performance_reasonable() -> None:
    # Performance: 1000 Kerzen, alle Indikatoren, klar unter der Schwelle.
    result = _engine().calculate(_big_frame(rows=1000))
    assert result.valid is True
    assert result.calculation_time < 2.0
