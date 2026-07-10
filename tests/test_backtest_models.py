"""Tests für die Backtest-Domänenmodelle (Eigenschaften, Report-Methoden)."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from models.backtest import (
    BacktestReport,
    BacktestResult,
    BenchmarkResult,
    Direction,
    EquityPoint,
    ExitReason,
    RecommendationStrength,
    TradeOutcome,
)
from models.recommendation import SuggestedAction
from tests.helpers import make_historical_signal, make_simulated_trade


def _result(symbol="AAPL", total_return_pct=5.0, benchmark=None):
    return BacktestResult(
        backtest_id=f"bt:{symbol}",
        symbol=symbol,
        timeframe="base",
        start_date=None,
        end_date=None,
        signal_count=3,
        trade_count=2,
        win_rate=0.5,
        loss_rate=0.5,
        profit_factor=1.5,
        average_win=10.0,
        average_loss=-5.0,
        average_risk_reward=2.0,
        average_holding_time=3.0,
        maximum_drawdown=4.0,
        expectancy=2.5,
        sharpe_ratio=None,
        sortino_ratio=None,
        calmar_ratio=None,
        total_return=50.0,
        total_return_pct=total_return_pct,
        final_equity=10500.0,
        benchmark=benchmark,
    )


def test_simulated_trade_is_win_loss():
    win = make_simulated_trade(profit=100.0)
    loss = make_simulated_trade(profit=-50.0)
    assert win.is_win and not win.is_loss
    assert loss.is_loss and not loss.is_win


def test_historical_signal_actionable_true():
    signal = make_historical_signal()
    assert signal.is_actionable is True


def test_historical_signal_neutral_not_actionable():
    signal = make_historical_signal(direction=Direction.NEUTRAL)
    assert signal.is_actionable is False


def test_historical_signal_wait_not_actionable():
    signal = make_historical_signal(action=SuggestedAction.WAIT)
    assert signal.is_actionable is False


def test_historical_signal_zero_shares_not_actionable():
    signal = make_historical_signal(shares=0.0)
    assert signal.is_actionable is False


def test_historical_signal_zero_stop_not_actionable():
    signal = make_historical_signal(stop_distance=0.0)
    assert signal.is_actionable is False


def test_report_by_symbol_filters():
    report = BacktestReport(results=[_result("AAPL"), _result("msft")])
    assert len(report.by_symbol("aapl")) == 1
    assert report.by_symbol("MSFT")[0].symbol == "msft"


def test_report_best_sorts_by_return():
    report = BacktestReport(results=[_result("A", 2.0), _result("B", 9.0), _result("C", 5.0)])
    best = report.best(2)
    assert [r.symbol for r in best] == ["B", "C"]


def test_report_backtest_count():
    report = BacktestReport(results=[_result("A"), _result("B")])
    assert report.backtest_count == 2


def test_result_outperformed_benchmark_none_without_benchmark():
    assert _result().outperformed_benchmark is None


def test_result_outperformed_benchmark_true():
    bench = BenchmarkResult("buy_and_hold", 100.0, 103.0, 10000.0, 10300.0, 3.0)
    assert _result(total_return_pct=5.0, benchmark=bench).outperformed_benchmark is True


def test_result_outperformed_benchmark_false():
    bench = BenchmarkResult("buy_and_hold", 100.0, 110.0, 10000.0, 11000.0, 10.0)
    assert _result(total_return_pct=5.0, benchmark=bench).outperformed_benchmark is False


def test_context_trade_count():
    from models.backtest import BacktestContext

    ctx = BacktestContext(
        symbol="AAPL",
        timeframe="base",
        starting_capital=10000.0,
        trades=[make_simulated_trade(), make_simulated_trade()],
        equity_curve=[],
    )
    assert ctx.trade_count == 2


@pytest.mark.parametrize(
    ("sample", "field_name"),
    [
        (make_simulated_trade(), "symbol"),
        (make_historical_signal(), "entry_price"),
        (EquityPoint(None, 100.0, 0.0, 0.0), "equity"),
        (BenchmarkResult("buy_and_hold", 1.0, 2.0, 10.0, 20.0, 100.0), "name"),
        (_result(), "symbol"),
        (BacktestReport(), "valid"),
    ],
)
def test_backtest_models_are_frozen(sample, field_name):
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(sample, field_name, "changed")


def test_enums_have_expected_values():
    assert Direction.LONG.value == "long"
    assert RecommendationStrength.VERY_HIGH.value == "very_high"
    assert TradeOutcome.WIN.value == "win"
    assert ExitReason.STOP.value == "stop"


def test_signal_and_trade_carry_transparency_fields():
    trade = make_simulated_trade()
    # Entry, Exit, Stop, Take Profit, Risk, Recommendation, Direction, Strength, Reasons.
    assert trade.entry_price and trade.exit_price and trade.stop_price
    assert trade.take_profit_price and trade.risk_amount >= 0
    assert trade.recommendation_id and trade.direction and trade.recommendation_strength
    assert isinstance(trade.reasons, list)
    assert isinstance(trade.entry_time, datetime | type(None))


def test_report_defaults_valid_empty():
    report = BacktestReport()
    assert report.valid is True
    assert report.results == []
    assert report.backtest_count == 0
    _ = UTC  # Import genutzt (Konsistenz mit anderen Testmodulen).
