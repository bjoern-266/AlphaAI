"""Tests des Universum-Aufbaus und des Universe-Loaders."""

from __future__ import annotations

from engines.market_discovery_registry import build_default_registry
from market_discovery.market_universe import apply_definition, build_universe
from market_discovery.universe_loader import UniverseLoader, empty_symbol_source
from models.market_discovery import MarketDefinition
from tests.market_discovery_helpers import make_symbol, make_symbol_source

_DAX = MarketDefinition("dax", "DAX", country="DE", exchange="XETRA")


def test_apply_definition_fills_gaps():
    symbol = make_symbol("SAP", country="", exchange="", market="")
    filled = apply_definition(symbol, _DAX)
    assert filled.market == "dax"
    assert filled.country == "DE"
    assert filled.exchange == "XETRA"


def test_apply_definition_keeps_existing():
    symbol = make_symbol("SAP", country="AT", exchange="VIE", market="custom")
    filled = apply_definition(symbol, _DAX)
    assert filled.country == "AT"
    assert filled.market == "custom"


def test_build_universe_dedupes():
    symbols = [make_symbol("A"), make_symbol("A"), make_symbol("B")]
    universe, warnings = build_universe(symbols, ["sp500"])
    assert universe.size == 2
    assert any("Doppelter" in w for w in warnings)


def test_build_universe_skips_empty_ticker():
    universe, warnings = build_universe([make_symbol("")], ["sp500"])
    assert universe.size == 0
    assert any("ohne Ticker" in w for w in warnings)


def test_loader_loads_registered_markets():
    universe_data = {"sp500": [make_symbol("AAPL"), make_symbol("MSFT")]}
    loader = UniverseLoader(build_default_registry(), make_symbol_source(universe_data))
    universe, warnings = loader.load(["sp500"])
    assert universe.size == 2
    assert universe.markets == ("sp500",)
    assert warnings == []


def test_loader_warns_unknown_market():
    loader = UniverseLoader(build_default_registry(), empty_symbol_source)
    universe, warnings = loader.load(["does_not_exist"])
    assert universe.size == 0
    assert any("Unbekannter Markt" in w for w in warnings)


def test_loader_tags_country_from_definition():
    data = {"dax": [make_symbol("SAP", country="", market="", exchange="")]}
    loader = UniverseLoader(build_default_registry(), make_symbol_source(data))
    universe, _ = loader.load(["dax"])
    assert universe.symbols[0].country == "DE"


def test_loader_dedupes_across_markets():
    data = {
        "sp500": [make_symbol("AAPL", market="")],
        "nasdaq100": [make_symbol("AAPL", market="")],
    }
    loader = UniverseLoader(build_default_registry(), make_symbol_source(data))
    universe, warnings = loader.load(["sp500", "nasdaq100"])
    assert universe.size == 1
    assert any("Doppelter" in w for w in warnings)


def test_loader_empty_source():
    loader = UniverseLoader(build_default_registry(), empty_symbol_source)
    universe, _ = loader.load(["sp500"])
    assert universe.size == 0
    assert universe.markets == ("sp500",)


def test_loader_multiple_markets_collects_all():
    data = {"sp500": [make_symbol("AAPL")], "dax": [make_symbol("SAP", market="")]}
    loader = UniverseLoader(build_default_registry(), make_symbol_source(data))
    universe, _ = loader.load(["sp500", "dax"])
    assert universe.size == 2
    assert set(universe.markets) == {"sp500", "dax"}
