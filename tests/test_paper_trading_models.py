"""Tests für die Paper-Trading-Domänenmodelle."""

from __future__ import annotations

import dataclasses

import pytest

from models.paper_trading import (
    CloseReason,
    Direction,
    JournalEntry,
    OrderAction,
    PaperEquityPoint,
    PaperOrder,
    PaperPerformance,
    PaperStatistics,
    PaperTradingReport,
    PaperTradingResult,
    PositionStatus,
    RecommendationStrength,
)
from tests.helpers import make_paper_position, make_paper_trade


def _result(status=PositionStatus.OPEN, symbol="AAPL"):
    return PaperTradingResult(
        paper_trading_id=f"paper:{symbol}",
        recommendation_id="rec:1",
        symbol=symbol,
        direction=Direction.LONG,
        recommendation_strength=RecommendationStrength.HIGH,
        status=status,
        entry_price=100.0,
        current_price=101.0,
        exit_price=0.0,
        position_size=1000.0,
        shares=10.0,
        fractional_shares=True,
        entry_time=None,
        exit_time=None,
        pnl=10.0,
        pnl_pct=1.0,
        running_drawdown=0.0,
        maximum_drawdown=0.0,
        current_equity=10010.0,
        portfolio_exposure=10.0,
    )


def test_enum_values():
    assert OrderAction.OPEN.value == "open"
    assert PositionStatus.CANCELLED.value == "cancelled"
    assert CloseReason.TAKE_PROFIT.value == "take_profit"


def test_position_is_open_property():
    pos = make_paper_position()
    assert pos.is_open is True
    assert pos.is_closed is False


def test_position_market_value():
    pos = make_paper_position(shares=10.0, entry_price=105.0)
    assert pos.market_value == 1050.0


def test_trade_win_loss_properties():
    assert make_paper_trade(pnl=10.0).is_win is True
    assert make_paper_trade(pnl=-10.0).is_loss is True
    assert make_paper_trade(pnl=-10.0).is_win is False


def test_report_by_status():
    report = PaperTradingReport(
        results=[_result(PositionStatus.OPEN), _result(PositionStatus.CLOSED)]
    )
    assert len(report.by_status(PositionStatus.OPEN)) == 1
    assert len(report.open_results) == 1
    assert len(report.closed_results) == 1


def test_report_result_count():
    report = PaperTradingReport(results=[_result(), _result()])
    assert report.result_count == 2


def test_report_defaults():
    report = PaperTradingReport()
    assert report.valid is True
    assert report.results == []
    assert isinstance(report.statistics, PaperStatistics)
    assert isinstance(report.performance, PaperPerformance)


def test_context_open_closed_partitions():
    from models.paper_trading import PaperTradingContext

    open_pos = make_paper_position(position_id="pos:AAPL:1")
    closed = dataclasses.replace(
        make_paper_position(position_id="pos:AAPL:2"), status=PositionStatus.CLOSED
    )
    ctx = PaperTradingContext(
        symbol="AAPL",
        timeframe="base",
        starting_capital=10000.0,
        current_equity=10000.0,
        positions=[open_pos, closed],
        trades=[],
        equity_curve=[],
    )
    assert len(ctx.open_positions) == 1
    assert len(ctx.closed_positions) == 1


@pytest.mark.parametrize(
    ("sample", "field_name"),
    [
        (make_paper_position(), "symbol"),
        (make_paper_trade(), "pnl"),
        (_result(), "symbol"),
        (PaperTradingReport(), "valid"),
        (PaperStatistics(), "win_rate"),
        (PaperPerformance(), "current_equity"),
        (PaperEquityPoint(None, 1.0, 0.0, 0.0, 0), "equity"),
        (
            PaperOrder(
                "o",
                "r",
                "p",
                OrderAction.OPEN,
                Direction.LONG,
                RecommendationStrength.HIGH,
                1.0,
                1.0,
            ),
            "price",
        ),
        (
            JournalEntry(
                "j",
                "p",
                "r",
                OrderAction.OPEN,
                Direction.LONG,
                RecommendationStrength.HIGH,
                1.0,
                0.0,
                "x",
            ),
            "reason",
        ),
    ],
)
def test_paper_models_are_frozen(sample, field_name):
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(sample, field_name, "changed")


def test_result_transparency_fields():
    result = _result()
    assert result.recommendation_id and result.direction and result.recommendation_strength
    assert result.paper_trading_id.startswith("paper:")
    assert result.fractional_shares is True
