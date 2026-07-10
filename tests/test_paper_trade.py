"""Tests für den Trade-Aufbau aus Positionen (paper_trading.trade)."""

from __future__ import annotations

from datetime import UTC, datetime

from models.paper_trading import CloseReason, PositionStatus
from paper_trading import position as pos_mod
from paper_trading import trade as trade_mod
from tests.helpers import make_paper_position

_ENTRY = datetime(2023, 1, 1, tzinfo=UTC)
_EXIT = datetime(2023, 1, 4, tzinfo=UTC)


def _closed(pnl_price=106.0):
    pos = make_paper_position(entry_price=100.0, shares=10.0, entry_time=_ENTRY)
    return pos_mod.close_position(pos, pnl_price, _EXIT, CloseReason.TAKE_PROFIT)


def test_trade_from_position_fields():
    trade = trade_mod.trade_from_position(_closed(), 2)
    assert trade.entry_price == 100.0
    assert trade.exit_price == 106.0
    assert trade.pnl == 60.0
    assert trade.close_reason is CloseReason.TAKE_PROFIT
    assert "2" in trade.trade_id


def test_trade_holding_time():
    trade = trade_mod.trade_from_position(_closed())
    assert trade.holding_time.days == 3


def test_trade_holding_time_none_without_timestamps():
    pos = make_paper_position(entry_time=None)
    closed = pos_mod.close_position(pos, 105.0, None, CloseReason.TAKE_PROFIT)
    trade = trade_mod.trade_from_position(closed)
    assert trade.holding_time is None


def test_trade_win_loss():
    assert trade_mod.trade_from_position(_closed(106.0)).is_win is True
    assert trade_mod.trade_from_position(_closed(94.0)).is_loss is True


def test_build_trades_only_closed():
    open_pos = make_paper_position(position_id="pos:AAPL:1")
    closed = _closed()
    trades = trade_mod.build_trades([open_pos, closed])
    assert len(trades) == 1
    assert trades[0].position_id == closed.position_id


def test_build_trades_empty():
    assert trade_mod.build_trades([]) == []


def test_build_trades_skips_cancelled():
    pos = make_paper_position()
    cancelled = pos_mod.cancel_position(pos, _EXIT)
    assert cancelled.status is PositionStatus.CANCELLED
    assert trade_mod.build_trades([cancelled]) == []


def test_trade_carries_transparency():
    trade = trade_mod.trade_from_position(_closed())
    assert trade.recommendation_id and trade.direction and trade.recommendation_strength
    assert trade.reasons == ["Testgrund"]
