"""Tests des Kandidaten-Vorfilters (reine Auswahl, Grenzwerte aus Regeln)."""

from __future__ import annotations

from market_discovery.candidate_filter import (
    CandidateFilter,
    apply_filter,
    load_candidate_filter,
)
from tests.market_discovery_helpers import make_symbol

_FILTER = CandidateFilter(
    min_price=1.0,
    min_volume=100_000.0,
    min_dollar_volume=1_000_000.0,
    min_history_days=200,
    require_tradable=True,
    exclude_delisted=True,
    exclude_penny=True,
    penny_price=1.0,
)


def test_clean_symbol_kept():
    assert _FILTER.reason(make_symbol()) is None


def test_not_tradable_rejected():
    assert _FILTER.reason(make_symbol(tradable=False)) == "nicht handelbar"


def test_delisted_rejected():
    assert _FILTER.reason(make_symbol(delisted=True)) == "delisted"


def test_missing_price_rejected():
    assert _FILTER.reason(make_symbol(price=None)) == "kein gültiger Kurs"


def test_negative_price_rejected():
    assert _FILTER.reason(make_symbol(price=-5.0)) == "ungültiger Kurs"


def test_penny_stock_rejected():
    assert _FILTER.reason(make_symbol(price=0.5)) == "Penny Stock"


def test_below_min_price_rejected():
    flt = CandidateFilter(min_price=50.0, exclude_penny=False)
    assert flt.reason(make_symbol(price=20.0)) == "Kurs unter Mindestwert"


def test_low_volume_rejected():
    assert _FILTER.reason(make_symbol(volume=1000.0)) == "Volumen zu gering"


def test_low_liquidity_rejected():
    assert _FILTER.reason(make_symbol(average_dollar_volume=1000.0)) == "Liquidität zu gering"


def test_short_history_rejected():
    assert _FILTER.reason(make_symbol(history_days=50)) == "Historie zu kurz"


def test_missing_volume_rejected_when_required():
    assert _FILTER.reason(make_symbol(volume=None)) == "Volumen zu gering"


def test_penny_allowed_when_disabled():
    flt = CandidateFilter(exclude_penny=False, min_price=None)
    assert flt.reason(make_symbol(price=0.5)) is None


def test_delisted_allowed_when_disabled():
    flt = CandidateFilter(exclude_delisted=False)
    assert flt.reason(make_symbol(delisted=True)) is None


def test_apply_filter_splits():
    symbols = [make_symbol("A"), make_symbol("B", price=0.5), make_symbol("C", delisted=True)]
    kept, rejected = apply_filter(symbols, _FILTER)
    assert [s.ticker for s in kept] == ["A"]
    assert {r.ticker for r in rejected} == {"B", "C"}


def test_apply_filter_rejection_reasons():
    _, rejected = apply_filter([make_symbol("B", price=0.5)], _FILTER)
    assert rejected[0].reason == "Penny Stock"


def test_load_candidate_filter_from_config():
    config = {
        "min_price": 2.0,
        "min_volume": 50_000,
        "min_dollar_volume": 500_000,
        "min_history_days": 100,
        "require_tradable": True,
        "exclude_delisted": True,
        "exclude_penny": True,
        "penny_price": 2.0,
    }
    flt = load_candidate_filter(config)
    assert flt.min_price == 2.0
    assert flt.min_history_days == 100
    assert flt.penny_price == 2.0


def test_load_candidate_filter_defaults_on_empty():
    flt = load_candidate_filter({})
    assert flt.min_price is None
    assert flt.require_tradable is True


def test_filter_is_frozen():
    import dataclasses

    import pytest

    with pytest.raises(dataclasses.FrozenInstanceError):
        _FILTER.min_price = 5.0  # type: ignore[misc]
