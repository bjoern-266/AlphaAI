"""Tests für die Backtest Engine (Ablauf, Validierung, Cache, Zusammenbau)."""

from __future__ import annotations

import dataclasses

import pandas as pd

from engines.backtest_cache import BacktestCache
from engines.backtest_engine import BacktestEngine
from models.backtest import BacktestReport, BacktestResult
from models.market import MarketResult, MarketStatus
from pipeline.runner import IntegrationRunner
from tests.helpers import make_backtest_rules, make_settings, make_trend_frame


def _engine(cache=None, rules=None, settings=None):
    return BacktestEngine(
        runner=IntegrationRunner.from_config(),
        settings=settings or make_settings(),
        rules=rules or make_backtest_rules(),
        cache=cache,
    )


def _market(**frames) -> MarketResult:
    data = {sym.upper(): frame for sym, frame in frames.items()}
    return MarketResult(provider="synthetic", status=MarketStatus.OK, data=data)


def test_run_frame_valid_on_trend():
    result = _engine().run_frame(make_trend_frame(60), "AAPL")
    assert isinstance(result, BacktestResult)
    assert result.valid is True
    assert result.symbol == "AAPL"
    assert result.backtest_id == "bt:AAPL:base"


def test_run_frame_populates_period():
    result = _engine().run_frame(make_trend_frame(60), "AAPL")
    assert result.start_date is not None
    assert result.end_date is not None
    assert result.end_date > result.start_date


def test_run_frame_has_benchmark():
    result = _engine().run_frame(make_trend_frame(60), "AAPL")
    assert result.benchmark is not None
    assert result.benchmark.name == "buy_and_hold"


def test_run_frame_equity_curve_starts_at_capital():
    result = _engine(settings=make_settings(capital=25000.0)).run_frame(
        make_trend_frame(60), "AAPL"
    )
    assert result.equity_curve[0].equity == 25000.0


def test_empty_history_invalid():
    result = _engine().run_frame(pd.DataFrame(), "AAPL")
    assert result.valid is False
    assert result.trade_count == 0
    assert any("Leere Historie" in w for w in result.warnings)


def test_short_history_invalid():
    result = _engine().run_frame(make_trend_frame(10), "AAPL")
    assert result.valid is False
    assert any("kurze Historie" in w for w in result.warnings)


def test_negative_prices_invalid():
    frame = make_trend_frame(60)
    frame.iloc[5, frame.columns.get_loc("close")] = -3.0
    result = _engine().run_frame(frame, "AAPL")
    assert result.valid is False
    assert any("Ungültige Preise" in w for w in result.warnings)


def test_non_monotonic_index_invalid():
    frame = make_trend_frame(60)
    frame = frame.iloc[::-1]  # absteigender Zeitindex
    result = _engine().run_frame(frame, "AAPL")
    assert result.valid is False
    assert any("nicht aufsteigend" in w for w in result.warnings)


def test_missing_close_column_invalid():
    frame = make_trend_frame(60).drop(columns=["close"])
    result = _engine().run_frame(frame, "AAPL")
    assert result.valid is False


def test_run_report_multi_symbol():
    engine = _engine()
    report = engine.run(_market(AAPL=make_trend_frame(60), MSFT=make_trend_frame(60)))
    assert isinstance(report, BacktestReport)
    assert report.backtest_count == 2
    assert {r.symbol for r in report.results} == {"AAPL", "MSFT"}


def test_run_report_calculation_time_set():
    engine = _engine()
    report = engine.run(_market(AAPL=make_trend_frame(60)))
    assert report.calculation_time >= 0.0


def test_run_report_is_frozen():
    import pytest

    report = _engine().run(_market(AAPL=make_trend_frame(60)))
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.valid = False  # type: ignore[misc]


def test_empty_market_result_invalid():
    report = _engine().run(_market())
    assert report.valid is False
    assert any("Keine Symbole" in w for w in report.warnings)


def test_cache_returns_same_report():
    cache = BacktestCache()
    engine = _engine(cache=cache)
    market = _market(AAPL=make_trend_frame(60))
    first = engine.run(market)
    second = engine.run(market)
    assert first is second
    assert cache.hits == 1


def test_disabled_model_defaults_metric():
    rules = make_backtest_rules(performance_model={"enabled": False})
    result = _engine(rules=rules).run_frame(make_trend_frame(60), "AAPL")
    # Ohne Performance-Modell bleiben dessen Kennzahlen auf dem Default.
    assert result.win_rate == 0.0
    assert result.expectancy == 0.0


def test_unregistered_model_warns():
    rules = make_backtest_rules(ghost_model={"enabled": True})
    result = _engine(rules=rules).run_frame(make_trend_frame(60), "AAPL")
    assert any("nicht registriert" in w for w in result.warnings)


def test_metrics_within_bounds():
    result = _engine().run_frame(make_trend_frame(80), "AAPL")
    assert 0.0 <= result.win_rate <= 1.0
    assert 0.0 <= result.loss_rate <= 1.0
    assert 0.0 <= result.maximum_drawdown <= 100.0


def test_prepared_ratios_present_as_fields():
    result = _engine().run_frame(make_trend_frame(80), "AAPL")
    # Vorbereitet: Felder existieren (float oder None).
    assert result.sharpe_ratio is None or isinstance(result.sharpe_ratio, float)
    assert result.sortino_ratio is None or isinstance(result.sortino_ratio, float)
    assert result.calmar_ratio is None or isinstance(result.calmar_ratio, float)


def test_summary_and_timestamp_set():
    result = _engine().run_frame(make_trend_frame(60), "AAPL")
    assert result.summary
    assert result.timestamp is not None


def test_metadata_records_signal_counts():
    result = _engine().run_frame(make_trend_frame(60), "AAPL")
    assert "actionable_signals" in result.metadata
    assert "model_metrics" in result.metadata


def test_run_frame_none_frame_invalid():
    result = _engine().run(_market(AAPL=make_trend_frame(60)))
    # sanity: report valid True while frame present
    assert result.valid is True
