"""Tests für das Quality-Score-Modell."""

from __future__ import annotations

import pytest

from scores.base import ScoreParameterError
from scores.quality_score import QualityScoreModel
from tests.helpers import make_components, make_score_context

WEIGHTS = {"indicator_quality": 0.4, "pattern_confidence": 0.4, "data_quality": 0.2}


def test_quality_weighted_sum() -> None:
    context = make_score_context(
        components=make_components(
            indicator_quality=100.0, pattern_confidence=50.0, data_quality=0.0
        )
    )
    output = QualityScoreModel().compute(context, WEIGHTS)
    # 0.4*100 + 0.4*50 + 0.2*0 = 60
    assert output.value == pytest.approx(60.0)


def test_quality_full() -> None:
    context = make_score_context(
        components=make_components(
            indicator_quality=100.0, pattern_confidence=100.0, data_quality=100.0
        )
    )
    assert QualityScoreModel().compute(context, WEIGHTS).value == pytest.approx(100.0)


def test_quality_reasons_present() -> None:
    output = QualityScoreModel().compute(make_score_context(), WEIGHTS)
    assert len(output.reasons) == 3


def test_quality_invalid_weights_raise() -> None:
    with pytest.raises(ScoreParameterError):
        QualityScoreModel().compute(make_score_context(), {**WEIGHTS, "data_quality": 0.5})
