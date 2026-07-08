"""Tests für gemeinsame Strategie-Hilfsmittel und -Typen."""

from __future__ import annotations

import pytest

from strategies.base import (
    StrategyContext,
    StrategyDirection,
    StrategyParameterError,
    build_hypothesis_id,
    direction_from_value,
    require_bool,
    require_float,
)
from tests.helpers import make_indicator_result, make_pattern_report, make_price_frame


def test_context_last_close_and_timestamp() -> None:
    frame = make_price_frame([100.0, 101.0, 102.0])
    context = StrategyContext(
        indicators=make_indicator_result(),
        patterns=make_pattern_report(),
        data=frame,
    )
    assert context.last_close == 102.0
    assert context.last_timestamp == frame.index[-1]


def test_context_without_data() -> None:
    context = StrategyContext(
        indicators=make_indicator_result(), patterns=make_pattern_report(), data=None
    )
    assert context.last_close is None
    assert context.last_timestamp is None


def test_direction_from_value() -> None:
    assert direction_from_value("bullish") is StrategyDirection.BULLISH
    assert direction_from_value("bearish") is StrategyDirection.BEARISH
    assert direction_from_value("anything") is StrategyDirection.NEUTRAL


def test_build_hypothesis_id_is_stable() -> None:
    a = build_hypothesis_id("s", StrategyDirection.BULLISH, "AAPL", None)
    b = build_hypothesis_id("s", StrategyDirection.BULLISH, "AAPL", None)
    assert a == b == "s:bullish:AAPL:na"


def test_require_float_and_bool_errors() -> None:
    with pytest.raises(StrategyParameterError):
        require_float({}, "x", "s")
    with pytest.raises(StrategyParameterError):
        require_float({"x": "nan"}, "x", "s")
    with pytest.raises(StrategyParameterError):
        require_bool({"x": 1}, "x", "s")
    assert require_float({"x": 2}, "x", "s") == 2.0
    assert require_bool({"x": True}, "x", "s") is True
