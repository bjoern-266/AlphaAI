"""Tests des Branchen-Ausgleichs (konfigurierbar, ordnet um, rechnet nicht)."""

from __future__ import annotations

from market_discovery.sector_balancer import BalanceConfig, balance, load_balance_config
from tests.market_intelligence_helpers import make_opportunity


def _sectors(opportunities):
    return [o.sector for o in opportunities]


def test_disabled_keeps_order():
    opps = [
        make_opportunity("A", score=90.0, sector="Semi"),
        make_opportunity("B", score=80.0, sector="Semi"),
        make_opportunity("C", score=70.0, sector="Semi"),
    ]
    result = balance(opps, BalanceConfig(enabled=False))
    assert [o.ticker for o in result] == ["A", "B", "C"]


def test_zero_streak_keeps_order():
    opps = [make_opportunity("A", sector="X"), make_opportunity("B", sector="X")]
    result = balance(opps, BalanceConfig(enabled=True, max_streak=0))
    assert [o.ticker for o in result] == ["A", "B"]


def test_breaks_long_streak():
    opps = [
        make_opportunity("A", score=95.0, sector="Semi"),
        make_opportunity("B", score=90.0, sector="Semi"),
        make_opportunity("C", score=85.0, sector="Semi"),
        make_opportunity("D", score=60.0, sector="Bank"),
    ]
    result = balance(opps, BalanceConfig(enabled=True, max_streak=2))
    # Nach zwei Semi wird die Bank (D) vorgezogen, bevor der dritte Semi (C) folgt.
    assert _sectors(result) == ["Semi", "Semi", "Bank", "Semi"]


def test_keeps_score_order_within_limit():
    opps = [
        make_opportunity("A", score=95.0, sector="Semi"),
        make_opportunity("B", score=90.0, sector="Bank"),
        make_opportunity("C", score=85.0, sector="Semi"),
    ]
    result = balance(opps, BalanceConfig(enabled=True, max_streak=2))
    assert [o.ticker for o in result] == ["A", "B", "C"]


def test_no_other_sector_available_keeps_order():
    opps = [make_opportunity(f"T{i}", score=100.0 - i, sector="Semi") for i in range(4)]
    result = balance(opps, BalanceConfig(enabled=True, max_streak=2))
    # Alle gleiche Branche -> keine Umordnung möglich.
    assert [o.ticker for o in result] == ["T0", "T1", "T2", "T3"]


def test_all_opportunities_preserved():
    opps = [make_opportunity(f"T{i}", sector=("Semi" if i % 2 else "Bank")) for i in range(6)]
    result = balance(opps, BalanceConfig(enabled=True, max_streak=1))
    assert {o.ticker for o in result} == {o.ticker for o in opps}
    assert len(result) == 6


def test_load_balance_config():
    config = load_balance_config({"enabled": False, "max_streak": 3})
    assert config.enabled is False
    assert config.max_streak == 3


def test_load_balance_config_defaults():
    config = load_balance_config({})
    assert config.enabled is True
    assert config.max_streak == 2


def test_empty_input():
    assert balance([], BalanceConfig()) == ()


def test_max_streak_one_alternates():
    opps = [
        make_opportunity("A", score=99.0, sector="Semi"),
        make_opportunity("B", score=98.0, sector="Semi"),
        make_opportunity("C", score=50.0, sector="Bank"),
    ]
    result = balance(opps, BalanceConfig(enabled=True, max_streak=1))
    # Nach einem Semi wird sofort die Bank vorgezogen.
    assert _sectors(result) == ["Semi", "Bank", "Semi"]
