"""Tests für das Confidence-Score-Modell."""

from __future__ import annotations

import pytest

from scores.base import ScoreParameterError
from scores.confidence_score import ConfidenceScoreModel
from strategies.base import StrategyDirection
from tests.helpers import make_components, make_score_context, make_strategy_result

WEIGHTS = {"strategy_confidence": 0.5, "pattern_confidence": 0.3, "consensus": 0.2}


def test_confidence_in_unit_range() -> None:
    sr = make_strategy_result(confidence=0.8, direction=StrategyDirection.BULLISH)
    context = make_score_context(
        strategy_result=sr,
        components=make_components(pattern_confidence=100.0),
        hypotheses=[sr],
    )
    output = ConfidenceScoreModel().compute(context, WEIGHTS)
    # 0.5*0.8 + 0.3*1.0 + 0.2*1.0 (consensus 1/1) = 0.9
    assert output.value == pytest.approx(0.9)


def test_confidence_full_consensus_and_confidence() -> None:
    sr = make_strategy_result(confidence=1.0)
    context = make_score_context(
        strategy_result=sr, components=make_components(pattern_confidence=100.0), hypotheses=[sr]
    )
    assert ConfidenceScoreModel().compute(context, WEIGHTS).value == pytest.approx(1.0)


def test_confidence_lower_with_disagreement() -> None:
    sr = make_strategy_result(confidence=0.6, direction=StrategyDirection.BULLISH)
    others = [make_strategy_result(direction=StrategyDirection.BEARISH) for _ in range(3)]
    context = make_score_context(
        strategy_result=sr,
        components=make_components(pattern_confidence=50.0),
        hypotheses=[sr, *others],
    )
    output = ConfidenceScoreModel().compute(context, WEIGHTS)
    assert output.value < 0.6


def test_confidence_invalid_weights_raise() -> None:
    with pytest.raises(ScoreParameterError):
        ConfidenceScoreModel().compute(make_score_context(), {"strategy_confidence": 1.0})
