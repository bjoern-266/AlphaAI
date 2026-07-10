"""Tests für das simulierte Paper-Portfolio (paper_trading.portfolio)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from core.exceptions import PaperTradingValidationError
from models.paper_trading import CloseReason, PositionStatus
from models.recommendation import Direction, RecommendationStrength
from paper_trading.portfolio import PaperPortfolio

_TS = datetime(2023, 1, 1, tzinfo=UTC)


def _portfolio(capital=10000.0, fractional=True):
    return PaperPortfolio(starting_capital=capital, fractional_shares=fractional)


def _open(
    portfolio, rec="rec:1", direction=Direction.LONG, entry=100.0, stop=96.0, tp=108.0, shares=10.0
):
    return portfolio.open_position(
        recommendation_id=rec,
        symbol="AAPL",
        direction=direction,
        recommendation_strength=RecommendationStrength.HIGH,
        entry_price=entry,
        stop_price=stop,
        take_profit_price=tp,
        shares=shares,
        risk_amount=shares * (entry - stop),
        entry_time=_TS,
        metadata={"entry_index": 0},
    )


def test_invalid_capital_raises():
    with pytest.raises(PaperTradingValidationError):
        PaperPortfolio(starting_capital=0.0)


def test_open_position_adds_open():
    p = _portfolio()
    pos = _open(p)
    assert pos.is_open
    assert len(p.open_positions()) == 1
    assert p.equity() == 10000.0


def test_open_records_order_and_journal():
    p = _portfolio()
    _open(p)
    assert len(p.orders) == 1
    assert len(p.journal) == 1


def test_duplicate_recommendation_raises():
    p = _portfolio()
    _open(p, rec="rec:dup")
    with pytest.raises(PaperTradingValidationError):
        _open(p, rec="rec:dup")


def test_negative_shares_raises():
    p = _portfolio()
    with pytest.raises(PaperTradingValidationError):
        _open(p, shares=-1.0)


def test_invalid_entry_price_raises():
    p = _portfolio()
    with pytest.raises(PaperTradingValidationError):
        _open(p, entry=0.0)


def test_negative_stop_raises():
    p = _portfolio()
    with pytest.raises(PaperTradingValidationError):
        _open(p, stop=-5.0)


def test_fractional_false_floors_shares():
    p = _portfolio(fractional=False)
    pos = _open(p, shares=10.7)
    assert pos.shares == 10.0


def test_fractional_true_keeps_fraction():
    p = _portfolio(fractional=True)
    pos = _open(p, shares=10.5)
    assert pos.shares == 10.5


def test_has_open_for_recommendation():
    p = _portfolio()
    _open(p, rec="rec:x")
    assert p.has_open_for_recommendation("rec:x") is True
    assert p.has_open_for_recommendation("rec:y") is False


def test_update_market_marks_to_market():
    p = _portfolio()
    _open(p, entry=100.0, shares=10.0)
    p.update_market(high=105.0, low=99.0, close=104.0, timestamp=_TS)
    assert p.equity() == pytest.approx(10040.0)
    assert p.open_positions()[0].current_price == 104.0


def test_update_market_closes_on_stop():
    p = _portfolio()
    _open(p, entry=100.0, stop=96.0, shares=10.0)
    closed = p.update_market(high=101.0, low=95.0, close=97.0, timestamp=_TS)
    assert len(closed) == 1
    assert closed[0].close_reason is CloseReason.STOP
    assert p.equity() == pytest.approx(9960.0)
    assert p.realized_pnl == pytest.approx(-40.0)


def test_update_market_closes_on_take_profit():
    p = _portfolio()
    _open(p, entry=100.0, tp=108.0, shares=10.0)
    closed = p.update_market(high=109.0, low=107.0, close=108.5, timestamp=_TS)
    assert closed[0].close_reason is CloseReason.TAKE_PROFIT
    assert p.realized_pnl == pytest.approx(80.0)


def test_exposure_after_open():
    p = _portfolio()
    _open(p, entry=100.0, shares=10.0)
    p.update_market(high=100.0, low=100.0, close=100.0, timestamp=_TS)
    # market value 1000 / equity 10000 = 10 %
    assert p.exposure_pct() == pytest.approx(10.0)


def test_exposure_zero_when_flat():
    p = _portfolio()
    assert p.exposure_pct() == 0.0


def test_drawdown_tracks_after_loss():
    p = _portfolio()
    _open(p, entry=100.0, stop=96.0, shares=10.0)
    p.update_market(high=101.0, low=95.0, close=97.0, timestamp=_TS)
    assert p.running_drawdown_pct() == pytest.approx(0.4)
    assert p.maximum_drawdown_pct == pytest.approx(0.4)


def test_equity_curve_grows_each_update():
    p = _portfolio()
    _open(p)
    p.update_market(high=101.0, low=99.0, close=100.0, timestamp=_TS)
    p.update_market(high=101.0, low=99.0, close=100.5, timestamp=_TS)
    # Ein Kapitalkurven-Punkt je Markt-Update.
    assert len(p.equity_curve) == 2


def test_context_for_open_position():
    p = _portfolio()
    pos = _open(p)
    ctx = p.context_for(pos.position_id)
    assert set(ctx) == {
        "current_equity",
        "portfolio_exposure",
        "running_drawdown",
        "maximum_drawdown",
    }


def test_close_position_manual():
    p = _portfolio()
    pos = _open(p, entry=100.0, shares=10.0)
    closed = p.close_position(pos.position_id, 103.0, _TS, CloseReason.MANUAL)
    assert closed.status is PositionStatus.CLOSED
    assert p.realized_pnl == pytest.approx(30.0)


def test_double_close_raises():
    p = _portfolio()
    pos = _open(p)
    p.close_position(pos.position_id, 103.0, _TS)
    with pytest.raises(PaperTradingValidationError):
        p.close_position(pos.position_id, 104.0, _TS)


def test_expire_uses_expire_reason():
    p = _portfolio()
    pos = _open(p)
    closed = p.close_position(pos.position_id, 101.0, _TS, CloseReason.EXPIRE)
    assert closed.close_reason is CloseReason.EXPIRE


def test_cancel_position():
    p = _portfolio()
    pos = _open(p)
    cancelled = p.cancel_position(pos.position_id, _TS)
    assert cancelled.status is PositionStatus.CANCELLED
    assert p.realized_pnl == 0.0


def test_cancel_then_close_raises():
    p = _portfolio()
    pos = _open(p)
    p.cancel_position(pos.position_id, _TS)
    with pytest.raises(PaperTradingValidationError):
        p.close_position(pos.position_id, 100.0, _TS)


def test_unknown_position_raises():
    p = _portfolio()
    with pytest.raises(PaperTradingValidationError):
        p.close_position("nope", 100.0, _TS)


def test_invalid_price_in_update_raises():
    p = _portfolio()
    _open(p)
    with pytest.raises(PaperTradingValidationError):
        p.update_market(high=-1.0, low=1.0, close=1.0, timestamp=_TS)


def test_positions_returns_all():
    p = _portfolio()
    a = _open(p, rec="rec:a")
    p.close_position(a.position_id, 100.0, _TS)
    _open(p, rec="rec:b")
    assert len(p.positions()) == 2
    assert len(p.open_positions()) == 1


def test_short_position_pnl_on_update():
    p = _portfolio()
    p.open_position(
        recommendation_id="rec:s",
        symbol="AAPL",
        direction=Direction.SHORT,
        recommendation_strength=RecommendationStrength.HIGH,
        entry_price=100.0,
        stop_price=104.0,
        take_profit_price=92.0,
        shares=10.0,
        risk_amount=40.0,
        entry_time=_TS,
        metadata={"entry_index": 0},
    )
    p.update_market(high=99.0, low=97.0, close=98.0, timestamp=_TS)
    # short profit: (100-98)*10 = 20
    assert p.equity() == pytest.approx(10020.0)


def test_close_records_order_and_journal():
    p = _portfolio()
    pos = _open(p)
    p.close_position(pos.position_id, 103.0, _TS)
    assert len(p.orders) == 2  # open + close
    assert len(p.journal) == 2
