"""Tests für das Order-Management und die Statuswechsel (paper_trading.order)."""

from __future__ import annotations

import pytest

from core.exceptions import PaperTradingValidationError
from models.paper_trading import OrderAction, PositionStatus
from paper_trading import order as order_mod
from tests.helpers import make_paper_position


def test_open_action_never_valid_on_existing():
    assert order_mod.is_valid_transition(PositionStatus.OPEN, OrderAction.OPEN) is False


def test_close_valid_on_open():
    assert order_mod.is_valid_transition(PositionStatus.OPEN, OrderAction.CLOSE) is True


def test_cancel_valid_on_open():
    assert order_mod.is_valid_transition(PositionStatus.OPEN, OrderAction.CANCEL) is True


def test_expire_valid_on_open():
    assert order_mod.is_valid_transition(PositionStatus.OPEN, OrderAction.EXPIRE) is True


def test_close_invalid_on_closed():
    assert order_mod.is_valid_transition(PositionStatus.CLOSED, OrderAction.CLOSE) is False


def test_any_invalid_on_cancelled():
    assert order_mod.is_valid_transition(PositionStatus.CANCELLED, OrderAction.CLOSE) is False


def test_ensure_valid_transition_raises():
    with pytest.raises(PaperTradingValidationError):
        order_mod.ensure_valid_transition(PositionStatus.CLOSED, OrderAction.CLOSE)


def test_ensure_valid_transition_ok():
    order_mod.ensure_valid_transition(PositionStatus.OPEN, OrderAction.CLOSE)  # kein Fehler


def test_target_status_close():
    assert order_mod.target_status(OrderAction.CLOSE) is PositionStatus.CLOSED


def test_target_status_cancel():
    assert order_mod.target_status(OrderAction.CANCEL) is PositionStatus.CANCELLED


def test_target_status_expire():
    assert order_mod.target_status(OrderAction.EXPIRE) is PositionStatus.CLOSED


def test_target_status_open_raises():
    with pytest.raises(PaperTradingValidationError):
        order_mod.target_status(OrderAction.OPEN)


def test_create_order_fields():
    pos = make_paper_position(recommendation_id="rec:9")
    order = order_mod.create_order(pos, OrderAction.OPEN, 100.0, None, "Eröffnung", 3)
    assert order.action is OrderAction.OPEN
    assert order.recommendation_id == "rec:9"
    assert order.position_id == pos.position_id
    assert order.price == 100.0
    assert "3" in order.order_id


def test_create_order_carries_direction_and_strength():
    pos = make_paper_position()
    order = order_mod.create_order(pos, OrderAction.CLOSE, 105.0, None, "stop", 0)
    assert order.direction is pos.direction
    assert order.recommendation_strength is pos.recommendation_strength
