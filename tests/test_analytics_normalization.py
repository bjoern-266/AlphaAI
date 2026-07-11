"""Tests für die Trade-Normalisierung (analytics.normalization)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from analytics import normalization as norm
from models.backtest import BacktestReport, BacktestResult, ExitReason, SimulatedTrade, TradeOutcome
from models.paper_trading import CloseReason, PaperTradingResult, PositionStatus
from models.recommendation import Direction, RecommendationStrength
from tests.helpers import make_simulated_trade


def _sim_trade(**over):
    defaults = dict(
        trade_id="bt:AAPL:1",
        symbol="AAPL",
        direction=Direction.LONG,
        recommendation_strength=RecommendationStrength.VERY_HIGH,
        recommendation_id="rec:score:trend_following:bullish:AAPL:2023-01-02T00:00:00",
        entry_time=datetime(2023, 1, 2, tzinfo=UTC),
        entry_price=100.0,
        exit_time=datetime(2023, 1, 5, tzinfo=UTC),
        exit_price=106.0,
        stop_price=98.0,
        take_profit_price=106.0,
        shares=10.0,
        risk_amount=20.0,
        position_value=1000.0,
        profit=60.0,
        profit_pct=6.0,
        return_on_risk=3.0,
        risk_reward=2.0,
        holding_bars=3,
        holding_time=timedelta(days=3),
        outcome=TradeOutcome.WIN,
        exit_reason=ExitReason.TAKE_PROFIT,
        reasons=["Score 73/100", "Risk LOW"],
        metadata={"pattern": "fvg"},
    )
    defaults.update(over)
    return SimulatedTrade(**defaults)


def _paper_result(**over):
    defaults = dict(
        paper_trading_id="paper:pos:AAPL:1",
        recommendation_id="rec:score:momentum:bearish:AAPL:2023-02-01T00:00:00",
        symbol="AAPL",
        direction=Direction.SHORT,
        recommendation_strength=RecommendationStrength.HIGH,
        status=PositionStatus.CLOSED,
        entry_price=100.0,
        current_price=95.0,
        exit_price=95.0,
        position_size=1000.0,
        shares=10.0,
        fractional_shares=True,
        entry_time=datetime(2023, 2, 1, tzinfo=UTC),
        exit_time=datetime(2023, 2, 3, tzinfo=UTC),
        pnl=50.0,
        pnl_pct=5.0,
        running_drawdown=0.0,
        maximum_drawdown=0.0,
        current_equity=10050.0,
        portfolio_exposure=0.0,
        close_reason=CloseReason.TAKE_PROFIT,
        reasons=["Score 61/100", "Risk MEDIUM"],
    )
    defaults.update(over)
    return PaperTradingResult(**defaults)


def test_from_backtest_maps_core_fields():
    trade = norm.from_backtest_trade(_sim_trade())
    assert trade.source == "backtest"
    assert trade.pnl == 60.0
    assert trade.direction is Direction.LONG
    assert trade.outcome == "win"
    assert trade.close_reason == "take_profit"


def test_from_backtest_derives_dimensions():
    trade = norm.from_backtest_trade(_sim_trade())
    assert trade.strategy == "trend_following"
    assert trade.risk_level == "low"
    assert trade.score == 73.0


def test_from_backtest_holding_days():
    trade = norm.from_backtest_trade(_sim_trade())
    assert trade.holding_days == 3.0


def test_from_backtest_labels_from_metadata():
    trade = norm.from_backtest_trade(_sim_trade())
    assert trade.labels.get("pattern") == "fvg"


def test_from_backtest_risk_reward_preserved():
    trade = norm.from_backtest_trade(_sim_trade())
    assert trade.risk_reward == 2.0
    assert trade.return_on_risk == 3.0


def test_from_paper_maps_core_fields():
    trade = norm.from_paper_result(_paper_result())
    assert trade.source == "paper_trading"
    assert trade.direction is Direction.SHORT
    assert trade.pnl == 50.0
    assert trade.outcome == "win"


def test_from_paper_derives_dimensions():
    trade = norm.from_paper_result(_paper_result())
    assert trade.strategy == "momentum"
    assert trade.risk_level == "medium"
    assert trade.score == 61.0


def test_from_paper_holding_days_from_times():
    trade = norm.from_paper_result(_paper_result())
    assert trade.holding_days == 2.0


def test_from_paper_zero_risk_reward():
    trade = norm.from_paper_result(_paper_result())
    assert trade.risk_reward == 0.0
    assert trade.return_on_risk == 0.0


def test_normalize_combines_reports():
    bt = BacktestReport(
        results=[
            BacktestResult(
                backtest_id="bt:AAPL:base",
                symbol="AAPL",
                timeframe="base",
                start_date=None,
                end_date=None,
                signal_count=1,
                trade_count=1,
                win_rate=1.0,
                loss_rate=0.0,
                profit_factor=2.0,
                average_win=60.0,
                average_loss=0.0,
                average_risk_reward=2.0,
                average_holding_time=3.0,
                maximum_drawdown=0.0,
                expectancy=60.0,
                sharpe_ratio=None,
                sortino_ratio=None,
                calmar_ratio=None,
                total_return=60.0,
                total_return_pct=0.6,
                final_equity=10060.0,
                trades=[_sim_trade()],
            )
        ]
    )
    from models.paper_trading import PaperTradingReport

    pt = PaperTradingReport(results=[_paper_result()])
    trades = norm.normalize(bt, pt)
    assert len(trades) == 2
    assert {t.source for t in trades} == {"backtest", "paper_trading"}


def test_normalize_none_reports():
    assert norm.normalize(None, None) == []


def test_normalize_only_closed_paper():
    from models.paper_trading import PaperTradingReport

    open_result = _paper_result(status=PositionStatus.OPEN, exit_time=None)
    pt = PaperTradingReport(results=[open_result])
    assert norm.normalize(None, pt) == []


def test_normalize_backtest_only_uses_helper():
    bt = BacktestReport(
        results=[
            BacktestResult(
                backtest_id="x",
                symbol="AAPL",
                timeframe="base",
                start_date=None,
                end_date=None,
                signal_count=1,
                trade_count=1,
                win_rate=1.0,
                loss_rate=0.0,
                profit_factor=2.0,
                average_win=100.0,
                average_loss=0.0,
                average_risk_reward=2.0,
                average_holding_time=3.0,
                maximum_drawdown=0.0,
                expectancy=100.0,
                sharpe_ratio=None,
                sortino_ratio=None,
                calmar_ratio=None,
                total_return=100.0,
                total_return_pct=1.0,
                final_equity=10100.0,
                trades=[make_simulated_trade()],
            )
        ]
    )
    trades = norm.normalize(bt, None)
    assert len(trades) == 1
    assert trades[0].source == "backtest"
