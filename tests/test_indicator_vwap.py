"""Tests für den VWAP-Indikator."""

from __future__ import annotations

import pytest

from indicators.vwap import VwapIndicator
from tests.helpers import make_price_frame


def test_vwap_constant_price() -> None:
    # Typischer Preis = (101 + 99 + 100) / 3 = 100 -> VWAP = 100.
    out = VwapIndicator().compute(make_price_frame([100.0] * 10), {})
    assert out.latest("vwap") == pytest.approx(100.0)


def test_vwap_requires_volume_flag() -> None:
    assert VwapIndicator().requires_volume is True


def test_vwap_weights_by_volume() -> None:
    # Zwei Kerzen mit unterschiedlichem Preis und Volumen.
    frame = make_price_frame([10.0, 20.0], volume=[1.0, 3.0])
    out = VwapIndicator().compute(frame, {})
    # typische Preise = 10 und 20; VWAP = (10*1 + 20*3) / (1+3) = 17.5
    assert out.latest("vwap") == pytest.approx(17.5)
