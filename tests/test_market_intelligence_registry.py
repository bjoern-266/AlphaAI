"""Tests der Bewertungsmodell-Registry (einzige Erweiterungsstelle)."""

from __future__ import annotations

import pytest

from core.exceptions import AlphaAIError, DuplicateRegistrationError
from engines.market_intelligence_registry import (
    MarketIntelligenceRegistry,
    build_default_registry,
)
from market_intelligence.base import BaseOpportunityModel
from market_intelligence.opportunity import RecommendationOpportunityModel
from models.opportunity import OpportunityModelOutput

_EXPECTED = {"recommendation", "risk", "analytics", "backtest", "paper_trading"}


def test_default_registry_has_five_models():
    registry = build_default_registry()
    assert set(registry.names()) == _EXPECTED


def test_default_registry_count():
    assert len(build_default_registry()) == 5


def test_registry_contains():
    registry = build_default_registry()
    assert "recommendation" in registry
    assert "does_not_exist" not in registry


def test_registry_get_returns_model():
    registry = build_default_registry()
    assert isinstance(registry.get("recommendation"), RecommendationOpportunityModel)


def test_registry_get_unknown_raises():
    with pytest.raises(AlphaAIError):
        build_default_registry().get("missing")


def test_registry_duplicate_raises():
    registry = MarketIntelligenceRegistry()
    registry.register(RecommendationOpportunityModel())
    with pytest.raises(DuplicateRegistrationError):
        registry.register(RecommendationOpportunityModel())


def test_custom_model_registration_without_engine_change():
    class CustomModel(BaseOpportunityModel):
        name = "custom"

        def compute(self, context, params):  # noqa: ANN001, D102
            return OpportunityModelOutput(self.name, 0.0, 0.0)

    registry = MarketIntelligenceRegistry()
    registry.register(CustomModel())
    assert "custom" in registry


def test_registry_names_sorted_unique():
    names = build_default_registry().names()
    assert names == sorted(names)
    assert len(names) == len(set(names))


def test_registered_model_name_matches():
    registry = build_default_registry()
    for name in registry.names():
        assert registry.get(name).name == name
