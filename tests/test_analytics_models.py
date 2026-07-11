"""Tests für die Analytics-Domänenmodelle."""

from __future__ import annotations

import dataclasses

import pytest

from models.analytics import (
    AnalyticsContext,
    AnalyticsModelOutput,
    AnalyticsReport,
    AnalyticsResult,
    Direction,
    GroupStatistics,
)
from tests.helpers import make_analytics_trade


def _result():
    return AnalyticsResult(
        analytics_id="analytics:bt:pt",
        backtest_id="bt",
        paper_trading_id="pt",
        trade_count=3,
        win_rate=0.66,
        loss_rate=0.33,
        profit_factor=2.0,
        expectancy=10.0,
        average_winner=20.0,
        average_loser=-10.0,
        maximum_drawdown=5.0,
        average_holding_time=3.0,
        average_risk_reward=2.0,
        long_statistics=GroupStatistics(label="long"),
        short_statistics=GroupStatistics(label="short"),
    )


def test_trade_win_loss_properties():
    assert make_analytics_trade(pnl=10.0, outcome="win").is_win is True
    assert make_analytics_trade(pnl=-10.0, outcome="loss").is_loss is True
    assert make_analytics_trade(pnl=-10.0, outcome="loss").is_win is False


def test_context_long_short_partitions():
    from models.recommendation import Direction as D

    ctx = AnalyticsContext(
        trades=[
            make_analytics_trade(direction=D.LONG),
            make_analytics_trade(direction=D.SHORT),
            make_analytics_trade(direction=D.LONG),
        ]
    )
    assert len(ctx.long_trades) == 2
    assert len(ctx.short_trades) == 1


def test_context_defaults():
    ctx = AnalyticsContext(trades=[])
    assert ctx.journal == ()
    assert ctx.backtest_id == ""
    assert ctx.timeframe == "base"


def test_report_trade_count_delegates():
    report = AnalyticsReport(result=_result())
    assert report.trade_count == 3


def test_report_defaults():
    report = AnalyticsReport(result=_result())
    assert report.valid is True
    assert report.model_outputs == {}


def test_group_statistics_defaults():
    stat = GroupStatistics(label="x")
    assert stat.trade_count == 0
    assert stat.profit_factor == 0.0


def test_model_output_defaults():
    out = AnalyticsModelOutput(name="m")
    assert out.metrics == {}
    assert out.statistics == {}


def test_direction_reexported():
    assert Direction.LONG.value == "long"


@pytest.mark.parametrize(
    ("sample", "field_name"),
    [
        (make_analytics_trade(), "symbol"),
        (GroupStatistics(label="x"), "label"),
        (AnalyticsModelOutput(name="m"), "name"),
        (AnalyticsContext(trades=[]), "timeframe"),
        (_result(), "analytics_id"),
        (AnalyticsReport(result=_result()), "valid"),
    ],
)
def test_analytics_models_are_frozen(sample, field_name):
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(sample, field_name, "changed")


def test_result_holds_all_dimension_dicts():
    result = _result()
    assert isinstance(result.strategy_statistics, dict)
    assert isinstance(result.pattern_statistics, dict)
    assert isinstance(result.risk_statistics, dict)
    assert isinstance(result.time_statistics, dict)
    assert isinstance(result.journal_statistics, dict)


def test_trade_carries_transparency():
    trade = make_analytics_trade()
    assert trade.recommendation_id
    assert trade.strategy and trade.risk_level
    assert trade.reasons
