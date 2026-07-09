"""Tests für das Consensus-Score-Modell."""

from __future__ import annotations

import pytest

from scores.consensus_score import ConsensusScoreModel
from strategies.base import StrategyDirection
from tests.helpers import make_score_context, make_strategy_result


def test_full_consensus() -> None:
    sr = make_strategy_result(direction=StrategyDirection.BULLISH)
    others = [make_strategy_result(direction=StrategyDirection.BULLISH) for _ in range(2)]
    context = make_score_context(strategy_result=sr, hypotheses=[sr, *others])
    output = ConsensusScoreModel().compute(context, {})
    assert output.value == pytest.approx(100.0)


def test_partial_consensus() -> None:
    sr = make_strategy_result(direction=StrategyDirection.BULLISH)
    others = [make_strategy_result(direction=StrategyDirection.BEARISH)]
    context = make_score_context(strategy_result=sr, hypotheses=[sr, *others])
    output = ConsensusScoreModel().compute(context, {})
    assert output.value == pytest.approx(50.0)


def test_single_hypothesis_warns() -> None:
    sr = make_strategy_result()
    context = make_score_context(strategy_result=sr, hypotheses=[sr])
    output = ConsensusScoreModel().compute(context, {})
    assert output.value == pytest.approx(100.0)
    assert output.warnings


def test_reasons_present() -> None:
    output = ConsensusScoreModel().compute(make_score_context(), {})
    assert output.reasons
