"""Tests für die Analytics Engine (Zusammenbau, Validierung, Cache, Registry)."""

from __future__ import annotations

import dataclasses

import pytest

from engines.analytics_cache import AnalyticsCache
from engines.analytics_engine import AnalyticsEngine
from models.analytics import AnalyticsReport
from models.backtest import BacktestReport, BacktestResult
from models.paper_trading import PaperTradingReport
from models.recommendation import Direction
from tests.helpers import make_analytics_rules, make_simulated_trade


def _bt_result(trades):
    return BacktestResult(
        backtest_id="bt:AAPL:base",
        symbol="AAPL",
        timeframe="base",
        start_date=None,
        end_date=None,
        signal_count=len(trades),
        trade_count=len(trades),
        win_rate=0.0,
        loss_rate=0.0,
        profit_factor=0.0,
        average_win=0.0,
        average_loss=0.0,
        average_risk_reward=0.0,
        average_holding_time=0.0,
        maximum_drawdown=0.0,
        expectancy=0.0,
        sharpe_ratio=None,
        sortino_ratio=None,
        calmar_ratio=None,
        total_return=0.0,
        total_return_pct=0.0,
        final_equity=10000.0,
        trades=list(trades),
    )


def _bt_report():
    trades = [
        make_simulated_trade(trade_id="a", direction=Direction.LONG, profit=100.0),
        make_simulated_trade(trade_id="b", direction=Direction.LONG, profit=-40.0),
        make_simulated_trade(trade_id="c", direction=Direction.SHORT, profit=60.0),
    ]
    return BacktestReport(results=[_bt_result(trades)])


def _engine(cache=None, rules=None):
    return AnalyticsEngine(rules=rules or make_analytics_rules(), cache=cache)


def test_analyze_returns_report():
    report = _engine().analyze(_bt_report())
    assert isinstance(report, AnalyticsReport)
    assert report.valid is True
    assert report.result.trade_count == 3


def test_analyze_assembles_core_metrics():
    result = _engine().analyze(_bt_report()).result
    assert result.win_rate == 2 / 3
    assert result.profit_factor == 160.0 / 40.0


def test_analyze_long_short_statistics():
    result = _engine().analyze(_bt_report()).result
    assert result.long_statistics.trade_count == 2
    assert result.short_statistics.trade_count == 1


def test_analyze_fills_all_dimensions():
    result = _engine().analyze(_bt_report()).result
    assert result.strategy_statistics
    assert result.recommendation_statistics
    assert result.risk_statistics
    assert result.time_statistics
    assert result.market_statistics
    assert result.summary


def test_analyze_performance_present():
    result = _engine().analyze(_bt_report()).result
    assert "total_return_pct" in result.performance


def test_analyze_none_reports_invalid():
    report = _engine().analyze(None, None)
    assert report.valid is False
    assert any("Weder Backtest" in w for w in report.warnings)


def test_analyze_no_trades_valid_but_warns():
    report = _engine().analyze(BacktestReport(results=[]))
    assert report.valid is True
    assert any("Keine Trades" in w for w in report.warnings)


def test_analyze_with_paper_report():
    paper = PaperTradingReport(metadata={"symbol": "AAPL"})
    report = _engine().analyze(None, paper)
    assert report.result.paper_trading_id == "paper:AAPL"


def test_report_is_frozen():
    report = _engine().analyze(_bt_report())
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.valid = False  # type: ignore[misc]


def test_calculation_time_set():
    report = _engine().analyze(_bt_report())
    assert report.calculation_time >= 0.0


def test_model_outputs_present():
    report = _engine().analyze(_bt_report())
    assert "trade_statistics" in report.model_outputs
    assert len(report.model_outputs) == 10


def test_cache_returns_same_report():
    cache = AnalyticsCache()
    engine = _engine(cache=cache)
    report_bt = _bt_report()
    first = engine.analyze(report_bt, symbol="AAPL")
    second = engine.analyze(report_bt, symbol="AAPL")
    assert first is second
    assert cache.hits == 1


def test_disabled_model_uses_fallback():
    rules = make_analytics_rules(trade_statistics={"enabled": False})
    result = _engine(rules=rules).analyze(_bt_report()).result
    # Ohne Trade-Statistics-Modell bleibt das Kern-Metrik-Fallback neutral.
    assert result.win_rate == 0.0
    assert result.trade_count == 3


def test_unregistered_model_warns():
    rules = make_analytics_rules(ghost_model={"enabled": True})
    report = _engine(rules=rules).analyze(_bt_report())
    assert any("nicht registriert" in w for w in report.warnings)


def test_analytics_id_format():
    result = _engine().analyze(_bt_report()).result
    assert result.analytics_id.startswith("analytics:")


def test_metadata_trade_count():
    report = _engine().analyze(_bt_report())
    assert report.metadata["trade_count"] == 3


def test_engine_from_config_builds():
    engine = AnalyticsEngine.from_config()
    report = engine.analyze(_bt_report())
    assert report.valid is True


def test_timestamp_set():
    result = _engine().analyze(_bt_report()).result
    assert result.timestamp is not None
