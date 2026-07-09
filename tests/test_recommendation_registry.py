"""Tests für die Recommendation-Registry."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from engines.recommendation_registry import RecommendationRegistry, build_default_registry
from recommendation.base import (
    BaseRecommendationModel,
    RecommendationContext,
    RecommendationModelOutput,
)
from recommendation.decision_model import DecisionModel

EXPECTED = {
    "decision_model",
    "recommendation_model",
    "confidence_model",
    "summary_model",
    "explanation_model",
}


class _DummyModel(BaseRecommendationModel):
    name = "dummy"

    def compute(
        self, context: RecommendationContext, params: Mapping[str, Any]
    ) -> RecommendationModelOutput:
        return RecommendationModelOutput(name=self.name)


def test_default_registry_contains_all_models() -> None:
    registry = build_default_registry()
    assert len(registry) == 5
    assert set(registry.names()) == EXPECTED


def test_register_duplicate_raises() -> None:
    registry = build_default_registry()
    with pytest.raises(ValueError, match="bereits registriert"):
        registry.register(DecisionModel())


def test_get_unknown_raises() -> None:
    with pytest.raises(KeyError):
        build_default_registry().get("does_not_exist")


def test_register_new_model() -> None:
    registry = RecommendationRegistry()
    registry.register(_DummyModel())
    assert "dummy" in registry
    assert registry.get("dummy").name == "dummy"
