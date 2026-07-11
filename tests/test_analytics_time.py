"""Tests für die Zeitanalyse (analytics.time_analysis)."""

from __future__ import annotations

from datetime import UTC, datetime

from analytics.time_analysis import TimeAnalysisModel
from tests.helpers import make_analytics_context, make_analytics_trade


def _trade_on(day: datetime, pnl: float = 10.0, holding: float = 2.0):
    return make_analytics_trade(entry_time=day, pnl=pnl, holding_days=holding)


def test_time_dimensions_present():
    out = TimeAnalysisModel().compute(make_analytics_context(), {})
    assert set(out.statistics) == {"weekday", "month", "hour", "holding"}


def test_weekday_grouping():
    # 2023-01-02 = Montag, 2023-01-03 = Dienstag
    trades = [
        _trade_on(datetime(2023, 1, 2, 9, tzinfo=UTC)),
        _trade_on(datetime(2023, 1, 3, 9, tzinfo=UTC)),
    ]
    out = TimeAnalysisModel().compute(make_analytics_context(trades=trades), {})
    assert set(out.statistics["weekday"]) == {"Mo", "Di"}


def test_month_grouping():
    trades = [
        _trade_on(datetime(2023, 1, 2, 9, tzinfo=UTC)),
        _trade_on(datetime(2023, 3, 2, 9, tzinfo=UTC)),
    ]
    out = TimeAnalysisModel().compute(make_analytics_context(trades=trades), {})
    assert set(out.statistics["month"]) == {"01", "03"}


def test_hour_grouping():
    trades = [
        _trade_on(datetime(2023, 1, 2, 9, tzinfo=UTC)),
        _trade_on(datetime(2023, 1, 2, 15, tzinfo=UTC)),
    ]
    out = TimeAnalysisModel().compute(make_analytics_context(trades=trades), {})
    assert set(out.statistics["hour"]) == {"09", "15"}


def test_holding_bands():
    trades = [
        make_analytics_trade(trade_id="a", holding_days=0.5),
        make_analytics_trade(trade_id="b", holding_days=2.0),
        make_analytics_trade(trade_id="c", holding_days=20.0),
    ]
    out = TimeAnalysisModel().compute(make_analytics_context(trades=trades), {})
    assert set(out.statistics["holding"]) == {"0-1", "1-3", ">7"}


def test_holding_bands_config():
    trades = [make_analytics_trade(holding_days=4.0)]
    ctx = make_analytics_context(trades=trades, config={"holding_bands": [2, 5]})
    out = TimeAnalysisModel().compute(ctx, {})
    assert set(out.statistics["holding"]) == {"2-5"}


def test_weekday_stats_have_pnl():
    trades = [_trade_on(datetime(2023, 1, 2, 9, tzinfo=UTC), pnl=100.0)]
    out = TimeAnalysisModel().compute(make_analytics_context(trades=trades), {})
    assert out.statistics["weekday"]["Mo"].total_pnl == 100.0


def test_time_no_entry_time_unknown():
    import dataclasses

    trades = [dataclasses.replace(make_analytics_trade(), entry_time=None)]
    out = TimeAnalysisModel().compute(make_analytics_context(trades=trades), {})
    assert "unbekannt" in out.statistics["weekday"]


def test_time_empty_context():
    out = TimeAnalysisModel().compute(make_analytics_context(trades=[]), {})
    assert out.statistics["weekday"] == {}


def test_metric_weekday_count():
    trades = [_trade_on(datetime(2023, 1, 2, 9, tzinfo=UTC))]
    out = TimeAnalysisModel().compute(make_analytics_context(trades=trades), {})
    assert out.metrics["weekday_count"] == 1.0
