"""Tests für die PatternEngine (Orchestrierung, Validierung, Cache)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from data.market_result import MarketResult, MarketStatus
from engines.pattern_cache import PatternCache
from engines.pattern_engine import PatternEngine, PatternRules, load_pattern_rules
from tests.helpers import make_price_frame


def _big_frame(rows: int = 120, seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    index = pd.date_range("2023-01-01", periods=rows, freq="D")
    close = 100.0 + np.cumsum(rng.normal(0.3, 1.5, rows))
    high = close + np.abs(rng.normal(0.8, 0.4, rows))
    low = close - np.abs(rng.normal(0.8, 0.4, rows))
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


def _engine(cache: PatternCache | None = None) -> PatternEngine:
    return PatternEngine(load_pattern_rules(), cache=cache)


def test_engine_detects_patterns() -> None:
    report = _engine().detect(_big_frame(), symbol="TEST")
    assert report.valid is True
    assert report.pattern_count > 0
    assert "fvg" in report.metadata["detected"]
    assert "overlapping_patterns" in report.metadata


def test_engine_records_calculation_time() -> None:
    report = _engine().detect(_big_frame())
    assert report.calculation_time >= 0.0


def test_engine_too_little_history_is_invalid() -> None:
    report = _engine().detect(make_price_frame([100.0] * 5))
    assert report.valid is False
    assert any("Zu wenig Historie" in w for w in report.warnings)


def test_engine_missing_columns_is_invalid() -> None:
    report = _engine().detect(pd.DataFrame({"close": [1.0, 2.0, 3.0]}))
    assert report.valid is False
    assert any("Pflichtspalten" in w for w in report.warnings)


def test_engine_invalid_series_is_flagged() -> None:
    frame = _big_frame()
    frame = frame.iloc[::-1]  # absteigender Index -> ungültige Zeitreihe
    report = _engine().detect(frame)
    assert report.valid is False
    assert any("Ungültige Zeitreihe" in w for w in report.warnings)


def test_engine_prepared_block_when_enabled_warns() -> None:
    rules = PatternRules(
        patterns={"order_block": {"enabled": True}},
        min_candles=1,
        version=1,
    )
    report = PatternEngine(rules).detect(_big_frame())
    assert any("nicht implementiert" in w for w in report.warnings)
    assert report.pattern_count == 0


def test_engine_uses_cache() -> None:
    cache = PatternCache()
    engine = _engine(cache=cache)
    frame = _big_frame()
    engine.detect(frame, symbol="X")
    engine.detect(frame, symbol="X")
    assert cache.hits == 1
    assert cache.misses == 1


def test_engine_detect_symbol_missing() -> None:
    empty = MarketResult(provider="yahoo", status=MarketStatus.EMPTY)
    report = _engine().detect_symbol(empty, "AAPL")
    assert report.valid is False
    assert any("Keine Marktdaten" in w for w in report.warnings)


def test_engine_detect_all_symbols() -> None:
    data = {"AAPL": _big_frame(seed=1), "MSFT": _big_frame(seed=2)}
    market = MarketResult(provider="yahoo", status=MarketStatus.OK, data=data)
    reports = _engine().detect_all(market)
    assert set(reports) == {"AAPL", "MSFT"}


def test_engine_overlap_count_present() -> None:
    report = _engine().detect(_big_frame())
    assert isinstance(report.metadata["overlapping_patterns"], int)
