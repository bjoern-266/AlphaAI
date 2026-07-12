"""Tests der Markt-Registry (einzige Erweiterungsstelle für Märkte)."""

from __future__ import annotations

import pytest

from core.exceptions import AlphaAIError, DuplicateRegistrationError
from engines.market_discovery_registry import (
    MarketDiscoveryRegistry,
    build_default_registry,
)
from models.market_discovery import MarketDefinition

_EXPECTED = {
    "nyse",
    "nasdaq",
    "sp500",
    "nasdaq100",
    "russell2000",
    "dax",
    "mdax",
    "sdax",
    "tecdax",
    "eurostoxx50",
}


def test_default_registry_has_all_markets():
    assert set(build_default_registry().names()) == _EXPECTED


def test_default_registry_count():
    assert len(build_default_registry()) == 10


def test_registry_contains():
    registry = build_default_registry()
    assert "dax" in registry
    assert "does_not_exist" not in registry


def test_registry_get_returns_definition():
    definition = build_default_registry().get("dax")
    assert isinstance(definition, MarketDefinition)
    assert definition.country == "DE"


def test_registry_get_unknown_raises():
    with pytest.raises(AlphaAIError):
        build_default_registry().get("missing")


def test_registry_duplicate_raises():
    registry = MarketDiscoveryRegistry()
    registry.register(MarketDefinition("dax"))
    with pytest.raises(DuplicateRegistrationError):
        registry.register(MarketDefinition("dax"))


def test_custom_market_registration_without_engine_change():
    registry = MarketDiscoveryRegistry()
    registry.register(MarketDefinition("tsx", "Toronto", country="CA"))
    assert "tsx" in registry


def test_us_markets_country():
    registry = build_default_registry()
    for key in ("nyse", "nasdaq", "sp500", "nasdaq100", "russell2000"):
        assert registry.get(key).country == "US"


def test_german_markets_country():
    registry = build_default_registry()
    for key in ("dax", "mdax", "sdax", "tecdax"):
        assert registry.get(key).country == "DE"


def test_registry_names_sorted():
    names = build_default_registry().names()
    assert names == sorted(names)
