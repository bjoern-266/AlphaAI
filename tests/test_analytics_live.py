"""Integrations-Tests: echte Backtest-/Paper-Reports durch die Analytics Engine.

Kein Mock: Backtest und Paper Trading laufen durch die **echte** Pipeline; das
Analytics-Framework wertet ausschließlich diese bestehenden Ergebnisse aus. Die
Tests belegen die Kern-Invarianten (nur Auswertung, keine Bewertung, keine
Veränderung, vollständige Nachvollziehbarkeit).
"""

from __future__ import annotations

import pytest

from engines.analytics_engine import AnalyticsEngine, load_analytics_rules
from engines.backtest_engine import BacktestEngine
from engines.paper_trading_engine import PaperTradingEngine
from models.market import MarketResult, MarketStatus
from pipeline.runner import IntegrationRunner
from tests import scenarios
from tests.helpers import make_backtest_rules, make_paper_rules, make_settings

_BT_RULES = make_backtest_rules(engine={"warmup_bars": 200, "step": 10, "min_history_bars": 210})
_PT_RULES = make_paper_rules(runner={"warmup_bars": 200, "step": 10, "max_holding_days": 8})


@pytest.fixture(scope="module")
def runner():
    return IntegrationRunner.from_config()


def _reports(runner, scenario):
    frame = scenario()
    bt = BacktestEngine(runner=runner, settings=make_settings(), rules=_BT_RULES)
    bt_report = bt.run(
        MarketResult(provider="synthetic", status=MarketStatus.OK, data={"AAPL": frame})
    )
    pt = PaperTradingEngine(runner=runner, settings=make_settings(), rules=_PT_RULES)
    pt_report = pt.run_frame(frame, "AAPL")
    return bt_report, pt_report


def _engine():
    return AnalyticsEngine(rules=load_analytics_rules())


def test_analyze_trend_up_valid(runner):
    bt, pt = _reports(runner, scenarios.trend_up)
    report = _engine().analyze(bt, pt, symbol="AAPL")
    assert report.valid is True
    assert report.result.trade_count >= 1


def test_trades_from_both_sources(runner):
    bt, pt = _reports(runner, scenarios.trend_up)
    report = _engine().analyze(bt, pt, symbol="AAPL")
    # LONG + SHORT decken alle Trades ab (trend_up erzeugt LONG).
    total = report.result.long_statistics.trade_count + report.result.short_statistics.trade_count
    assert total == report.result.trade_count


def test_strategy_derived_from_real_data(runner):
    bt, pt = _reports(runner, scenarios.trend_up)
    result = _engine().analyze(bt, pt, symbol="AAPL").result
    # Aus der echten recommendation_id abgeleitet – keine 'unbekannt'-Strategie.
    assert "unbekannt" not in result.strategy_statistics


def test_risk_level_derived_from_real_data(runner):
    bt, pt = _reports(runner, scenarios.trend_up)
    result = _engine().analyze(bt, pt, symbol="AAPL").result
    assert any(level in result.risk_statistics for level in ("low", "medium", "high"))


def test_short_scenario_direction(runner):
    bt, pt = _reports(runner, scenarios.trend_down)
    result = _engine().analyze(bt, pt, symbol="XYZ").result
    assert result.long_statistics.trade_count == 0


def test_journal_statistics_from_paper(runner):
    bt, pt = _reports(runner, scenarios.trend_up)
    result = _engine().analyze(bt, pt, symbol="AAPL").result
    assert result.journal_statistics.get("total_entries", 0) >= 1


def test_reproducible_result(runner):
    bt, pt = _reports(runner, scenarios.trend_up)
    engine = _engine()
    first = engine.analyze(bt, pt, symbol="AAPL").result
    second = engine.analyze(bt, pt, symbol="AAPL").result
    assert first.win_rate == second.win_rate
    assert first.profit_factor == second.profit_factor
    assert first.trade_count == second.trade_count


def test_summary_present(runner):
    bt, pt = _reports(runner, scenarios.trend_up)
    result = _engine().analyze(bt, pt, symbol="AAPL").result
    assert "Trades ausgewertet" in result.summary


def test_backtest_only_analysis(runner):
    bt, _ = _reports(runner, scenarios.trend_up)
    report = _engine().analyze(bt, None, symbol="AAPL")
    assert report.valid is True
    assert report.result.journal_statistics.get("total_entries", 0) == 0


def test_metrics_within_bounds(runner):
    bt, pt = _reports(runner, scenarios.sideways)
    result = _engine().analyze(bt, pt, symbol="SYM").result
    assert 0.0 <= result.win_rate <= 1.0
    assert 0.0 <= result.maximum_drawdown <= 100.0
