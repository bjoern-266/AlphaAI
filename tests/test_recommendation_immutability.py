"""Tests: alle Recommendation-Datenmodelle sind unveränderlich (frozen)."""

from __future__ import annotations

import dataclasses

import pytest

from models.recommendation import (
    Direction,
    RecommendationFactor,
    RecommendationModelOutput,
    RecommendationReport,
    RecommendationResult,
    RecommendationStrength,
    SuggestedAction,
)

FROZEN_SAMPLES = [
    RecommendationFactor("score", 80.0, "reason"),
    RecommendationModelOutput(name="m"),
    RecommendationResult(
        recommendation_id="rec:x",
        risk_id="risk:x",
        score_id="score:x",
        hypothesis_id="h",
        direction=Direction.LONG,
        recommendation_strength=RecommendationStrength.LOW,
        confidence=0.5,
        overall_rating=40.0,
        suggested_action=SuggestedAction.WAIT,
    ),
    RecommendationReport(),
]


@pytest.mark.parametrize("obj", FROZEN_SAMPLES, ids=lambda o: type(o).__name__)
def test_recommendation_models_are_frozen(obj: object) -> None:
    assert type(obj).__dataclass_params__.frozen is True
    first_field = dataclasses.fields(obj)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(obj, first_field, getattr(obj, first_field))
