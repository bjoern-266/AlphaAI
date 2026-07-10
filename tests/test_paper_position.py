"""Tests für das Positions-Management (paper_trading.position)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from models.paper_trading import CloseReason, PositionStatus
from models.recommendation import Direction
from paper_trading import position as pos_mod
from tests.helpers import make_paper_position

_TS = datetime(2023, 1, 2, tzinfo=UTC)


def test_compute_pnl_long():
    assert pos_mod.compute_pnl(Direction.LONG, 100.0, 105.0, 10.0) == 50.0


def test_compute_pnl_short():
    assert pos_mod.compute_pnl(Direction.SHORT, 100.0, 95.0, 10.0) == 50.0


def test_compute_pnl_short_loss():
    assert pos_mod.compute_pnl(Direction.SHORT, 100.0, 105.0, 10.0) == -50.0


def test_open_position_defaults():
    pos = make_paper_position(entry_price=100.0, shares=10.0)
    assert pos.status is PositionStatus.OPEN
    assert pos.current_price == 100.0
    assert pos.position_size == 1000.0
    assert pos.exit_price == 0.0


def test_mark_to_market_updates_pnl():
    pos = make_paper_position(entry_price=100.0, shares=10.0)
    marked = pos_mod.mark_to_market(pos, 105.0, _TS)
    assert marked.current_price == 105.0
    assert marked.pnl == 50.0
    assert marked.pnl_pct == pytest.approx(5.0)


def test_mark_to_market_closed_is_noop():
    pos = make_paper_position()
    closed = pos_mod.close_position(pos, 105.0, _TS, CloseReason.TAKE_PROFIT)
    again = pos_mod.mark_to_market(closed, 200.0, _TS)
    assert again.current_price == 105.0


def test_detect_exit_long_stop():
    pos = make_paper_position(direction=Direction.LONG, stop_price=96.0, take_profit_price=108.0)
    reason, price = pos_mod.detect_exit(pos, high=101.0, low=95.0, close=100.0)
    assert reason is CloseReason.STOP
    assert price == 96.0


def test_detect_exit_long_take_profit():
    pos = make_paper_position(direction=Direction.LONG, stop_price=96.0, take_profit_price=108.0)
    reason, price = pos_mod.detect_exit(pos, high=109.0, low=99.0, close=108.5)
    assert reason is CloseReason.TAKE_PROFIT
    assert price == 108.0


def test_detect_exit_long_stop_priority():
    pos = make_paper_position(direction=Direction.LONG, stop_price=96.0, take_profit_price=108.0)
    reason, _ = pos_mod.detect_exit(pos, high=109.0, low=95.0, close=100.0)
    assert reason is CloseReason.STOP


def test_detect_exit_short_stop():
    pos = make_paper_position(direction=Direction.SHORT, stop_price=104.0, take_profit_price=92.0)
    reason, price = pos_mod.detect_exit(pos, high=105.0, low=99.0, close=100.0)
    assert reason is CloseReason.STOP
    assert price == 104.0


def test_detect_exit_short_take_profit():
    pos = make_paper_position(direction=Direction.SHORT, stop_price=104.0, take_profit_price=92.0)
    reason, price = pos_mod.detect_exit(pos, high=101.0, low=91.0, close=93.0)
    assert reason is CloseReason.TAKE_PROFIT
    assert price == 92.0


def test_detect_exit_none():
    pos = make_paper_position(direction=Direction.LONG, stop_price=96.0, take_profit_price=108.0)
    reason, price = pos_mod.detect_exit(pos, high=103.0, low=99.0, close=101.0)
    assert reason is None
    assert price == 101.0


def test_close_position_realizes_pnl():
    pos = make_paper_position(entry_price=100.0, shares=10.0)
    closed = pos_mod.close_position(pos, 106.0, _TS, CloseReason.TAKE_PROFIT)
    assert closed.status is PositionStatus.CLOSED
    assert closed.exit_price == 106.0
    assert closed.exit_time == _TS
    assert closed.close_reason is CloseReason.TAKE_PROFIT
    assert closed.pnl == 60.0


def test_cancel_position():
    pos = make_paper_position()
    cancelled = pos_mod.cancel_position(pos, _TS)
    assert cancelled.status is PositionStatus.CANCELLED
    assert cancelled.pnl == 0.0


def test_trailing_stop_inactive_by_default():
    pos = make_paper_position(direction=Direction.LONG, stop_price=96.0)
    same = pos_mod.apply_trailing_stop(pos, 110.0, 0.0)
    assert same.stop_price == 96.0


def test_trailing_stop_long_ratchets_up():
    pos = make_paper_position(direction=Direction.LONG, stop_price=96.0)
    trailed = pos_mod.apply_trailing_stop(pos, 110.0, 5.0)
    assert trailed.stop_price == 105.0
    assert trailed.trailing_stop_price == 105.0


def test_trailing_stop_long_never_lowers():
    pos = make_paper_position(direction=Direction.LONG, stop_price=104.0)
    trailed = pos_mod.apply_trailing_stop(pos, 106.0, 5.0)
    # candidate 101 < current stop 104 -> unverändert
    assert trailed.stop_price == 104.0


def test_trailing_stop_short_ratchets_down():
    pos = make_paper_position(direction=Direction.SHORT, stop_price=110.0)
    trailed = pos_mod.apply_trailing_stop(pos, 100.0, 5.0)
    assert trailed.stop_price == 105.0


def test_open_position_is_immutable():
    import dataclasses

    pos = make_paper_position()
    with pytest.raises(dataclasses.FrozenInstanceError):
        pos.entry_price = 1.0
