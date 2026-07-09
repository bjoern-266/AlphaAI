"""Tests für das Weighted-Score-Modell."""

from __future__ import annotations

import pytest

from scores.base import ScoreParameterError
from scores.weighted_score import WeightedScoreModel
from tests.helpers import make_components, make_score_context

WEIGHTS8 = {
    "trend": 0.2,
    "momentum": 0.2,
    "pattern_strength": 0.15,
    "pattern_confidence": 0.1,
    "indicator_quality": 0.1,
    "market_context": 0.1,
    "volume_quality": 0.075,
    "data_quality": 0.075,
}


def test_all_components_hundred_gives_hundred() -> None:
    context = make_score_context(components=make_components(**dict.fromkeys(WEIGHTS8, 100.0)))
    output = WeightedScoreModel().compute(context, WEIGHTS8)
    assert output.value == pytest.approx(100.0)


def test_all_components_zero_gives_zero() -> None:
    context = make_score_context(components=make_components(**dict.fromkeys(WEIGHTS8, 0.0)))
    output = WeightedScoreModel().compute(context, WEIGHTS8)
    assert output.value == pytest.approx(0.0)


def test_reasons_show_transparent_breakdown() -> None:
    context = make_score_context(components=make_components(trend=90.0))
    output = WeightedScoreModel().compute(context, WEIGHTS8)
    # Trend-Gewicht 0.2 -> max 20; Wert 90 -> Beitrag 18 -> "trend: 18/20".
    assert any(r == "trend: 18/20" for r in output.reasons)
    assert "trend" in output.details


def test_invalid_weights_raise() -> None:
    context = make_score_context()
    with pytest.raises(ScoreParameterError):
        WeightedScoreModel().compute(context, {**WEIGHTS8, "trend": 0.9})
