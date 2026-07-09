"""Tests für das Market-Score-Modell."""

from __future__ import annotations

import pytest

from scores.base import ScoreParameterError
from scores.market_score import MarketScoreModel
from tests.helpers import make_components, make_score_context

WEIGHTS = {"market_context": 0.6, "volume_quality": 0.4}


def test_market_weighted_sum() -> None:
    context = make_score_context(
        components=make_components(market_context=100.0, volume_quality=50.0)
    )
    output = MarketScoreModel().compute(context, WEIGHTS)
    # 0.6*100 + 0.4*50 = 80
    assert output.value == pytest.approx(80.0)


def test_market_full() -> None:
    context = make_score_context(
        components=make_components(market_context=100.0, volume_quality=100.0)
    )
    assert MarketScoreModel().compute(context, WEIGHTS).value == pytest.approx(100.0)


def test_market_reasons_present() -> None:
    output = MarketScoreModel().compute(make_score_context(), WEIGHTS)
    assert len(output.reasons) == 2


def test_market_invalid_weights_raise() -> None:
    with pytest.raises(ScoreParameterError):
        MarketScoreModel().compute(make_score_context(), {"market_context": 0.6})
