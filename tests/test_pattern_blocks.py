"""Tests für die vorbereiteten Block-Muster (noch keine Erkennung)."""

from __future__ import annotations

import pytest

from patterns.breaker_block import BreakerBlockPattern
from patterns.mitigation_block import MitigationBlockPattern
from patterns.order_block import OrderBlockPattern
from tests.helpers import make_price_frame

_BLOCKS = [OrderBlockPattern, BreakerBlockPattern, MitigationBlockPattern]


@pytest.mark.parametrize("block_cls", _BLOCKS)
def test_blocks_are_not_implemented(block_cls: type) -> None:
    block = block_cls()
    assert block.implemented is False


@pytest.mark.parametrize("block_cls", _BLOCKS)
def test_blocks_detect_nothing_but_warn(block_cls: type) -> None:
    frame = make_price_frame([10.0] * 5)
    detection = block_cls().detect(frame, {})
    assert detection.patterns == []
    assert detection.warnings
