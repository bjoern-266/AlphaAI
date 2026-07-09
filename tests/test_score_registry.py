"""Tests für die Score-Registry."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from engines.score_registry import ScoreRegistry, build_default_registry
from scores.base import BaseScoreModel, ScoreContext, ScoreModelOutput
from scores.weighted_score import WeightedScoreModel

EXPECTED = {
    "weighted_score",
    "confidence_score",
    "quality_score",
    "consensus_score",
    "market_score",
}


class _DummyModel(BaseScoreModel):
    name = "dummy"

    def compute(self, context: ScoreContext, params: Mapping[str, Any]) -> ScoreModelOutput:
        return ScoreModelOutput(name=self.name, value=0.0)


def test_default_registry_contains_all_models() -> None:
    registry = build_default_registry()
    assert len(registry) == 5
    assert set(registry.names()) == EXPECTED


def test_each_model_has_value_range() -> None:
    registry = build_default_registry()
    for name in registry.names():
        assert registry.get(name).value_range


def test_register_duplicate_raises() -> None:
    registry = build_default_registry()
    with pytest.raises(ValueError, match="bereits registriert"):
        registry.register(WeightedScoreModel())


def test_get_unknown_raises() -> None:
    with pytest.raises(KeyError):
        build_default_registry().get("does_not_exist")


def test_register_new_model() -> None:
    registry = ScoreRegistry()
    registry.register(_DummyModel())
    assert "dummy" in registry
    assert registry.get("dummy").name == "dummy"
