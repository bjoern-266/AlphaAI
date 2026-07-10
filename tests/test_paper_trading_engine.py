"""Tests für die Paper Trading Engine (Ablauf, Validierung, Cache, Report)."""

from __future__ import annotations

import dataclasses

import pandas as pd
import pytest

from engines.paper_trading_cache import PaperTradingCache
from engines.paper_trading_engine import PaperTradingEngine
from models.market import MarketResult, MarketStatus
from models.paper_trading import PaperTradingReport
from pipeline.runner import IntegrationRunner
from tests.helpers import make_paper_rules, make_settings, make_trend_frame

# Realistischer Vorlauf (genug Historie für EMA200), größere Schrittweite = schnell.
_RULES = make_paper_rules(
    runner={"warmup_bars": 200, "step": 10, "max_holding_days": 8, "trailing_distance": 0.0}
)


def _engine(cache=None, rules=None, settings=None):
    return PaperTradingEngine(
        runner=IntegrationRunner.from_config(),
        settings=settings or make_settings(),
        rules=rules or _RULES,
        cache=cache,
    )


def _market(**frames) -> MarketResult:
    data = {sym.upper(): frame for sym, frame in frames.items()}
    return MarketResult(provider="synthetic", status=MarketStatus.OK, data=data)


def test_run_frame_valid_on_trend():
    report = _engine().run_frame(make_trend_frame(240), "AAPL")
    assert isinstance(report, PaperTradingReport)
    assert report.valid is True


def test_run_frame_produces_positions():
    report = _engine().run_frame(make_trend_frame(240), "AAPL")
    assert report.result_count >= 1
    assert len(report.journal) >= 1
    assert len(report.orders) >= 1


def test_empty_history_invalid():
    report = _engine().run_frame(pd.DataFrame(), "AAPL")
    assert report.valid is False
    assert report.result_count == 0


def test_missing_close_invalid():
    report = _engine().run_frame(make_trend_frame(240).drop(columns=["close"]), "AAPL")
    assert report.valid is False


def test_negative_price_invalid():
    frame = make_trend_frame(240)
    frame.iloc[5, frame.columns.get_loc("close")] = -3.0
    report = _engine().run_frame(frame, "AAPL")
    assert report.valid is False


def test_non_monotonic_invalid():
    frame = make_trend_frame(240).iloc[::-1]
    report = _engine().run_frame(frame, "AAPL")
    assert report.valid is False


def test_run_single_symbol_report():
    report = _engine().run(_market(AAPL=make_trend_frame(240)))
    assert report.valid is True
    assert report.metadata["symbol"] == "AAPL"


def test_run_multi_symbol_shared_portfolio():
    report = _engine().run(_market(AAPL=make_trend_frame(240), MSFT=make_trend_frame(240)))
    assert report.valid is True
    # gemeinsames Depot: Startkapital bleibt das der Settings
    assert report.performance.starting_capital == make_settings().account.capital


def test_run_empty_market_invalid():
    report = _engine().run(_market())
    assert report.valid is False


def test_run_report_calculation_time():
    report = _engine().run(_market(AAPL=make_trend_frame(240)))
    assert report.calculation_time >= 0.0


def test_run_report_is_frozen():
    report = _engine().run(_market(AAPL=make_trend_frame(240)))
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.valid = False  # type: ignore[misc]


def test_cache_returns_same_report():
    cache = PaperTradingCache()
    engine = _engine(cache=cache)
    market = _market(AAPL=make_trend_frame(240))
    first = engine.run(market)
    second = engine.run(market)
    assert first is second
    assert cache.hits == 1


def test_statistics_and_performance_present():
    report = _engine().run_frame(make_trend_frame(240), "AAPL")
    assert 0.0 <= report.statistics.win_rate <= 1.0
    assert report.performance.current_equity > 0.0
    assert 0.0 <= report.performance.maximum_drawdown_pct <= 100.0


def test_disabled_statistics_model_fallback():
    rules = make_paper_rules(
        runner={"warmup_bars": 200, "step": 10}, statistics_model={"enabled": False}
    )
    report = _engine(rules=rules).run_frame(make_trend_frame(240), "AAPL")
    # Fallback-Statistik ist neutral, aber Kapital ist gesetzt.
    assert report.statistics.win_rate == 0.0
    assert report.statistics.current_equity > 0.0


def test_unregistered_model_warns():
    rules = make_paper_rules(runner={"warmup_bars": 200, "step": 10}, ghost_model={"enabled": True})
    report = _engine(rules=rules).run_frame(make_trend_frame(240), "AAPL")
    assert any("nicht registriert" in w for w in report.warnings)


def test_result_fields_mapping():
    report = _engine().run_frame(make_trend_frame(240), "AAPL")
    result = report.results[0]
    assert result.recommendation_id.startswith("rec:")
    assert result.paper_trading_id.startswith("paper:")
    assert result.fractional_shares is True
    assert result.current_equity > 0.0


def test_metadata_contains_model_metrics():
    report = _engine().run_frame(make_trend_frame(240), "AAPL")
    assert "model_metrics" in report.metadata
    assert "statistics_model" in report.metadata["model_metrics"]


def test_fractional_false_setting_floors_shares():
    settings = make_settings(fractional=False)
    report = _engine(settings=settings).run_frame(make_trend_frame(240), "AAPL")
    for result in report.results:
        assert result.shares == float(int(result.shares))
