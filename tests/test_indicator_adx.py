"""Tests für den ADX-Indikator."""

from __future__ import annotations

from indicators.adx import AdxIndicator
from tests.helpers import make_price_frame


def test_adx_within_valid_range() -> None:
    frame = make_price_frame([100.0 + i for i in range(60)])
    out = AdxIndicator().compute(frame, {"period": 14})
    adx = out.latest("adx")
    assert adx is not None
    assert 0.0 <= adx <= 100.0


def test_adx_provides_directional_indices() -> None:
    frame = make_price_frame([100.0 + i for i in range(60)])
    out = AdxIndicator().compute(frame, {"period": 14})
    assert set(out.series) == {"adx", "plus_di", "minus_di"}
    # Aufwärtstrend: +DI sollte über -DI liegen.
    assert out.latest("plus_di") > out.latest("minus_di")


def test_adx_min_candles() -> None:
    assert AdxIndicator().min_candles({"period": 14}) == 28
