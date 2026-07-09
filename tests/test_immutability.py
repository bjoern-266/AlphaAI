"""Tests: alle Ergebnis-Datenmodelle sind unveränderlich (frozen).

Stellt sicher, dass die Domänenmodelle nach ihrer Erstellung nicht mehr per
Attribut-Zuweisung verändert werden können – die Grundlage dafür, dass keine
Engine ihre Ergebnisse nachträglich mutiert.
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from models.indicator import IndicatorOutput, IndicatorResult
from models.market import MarketResult, MarketStatus
from models.pattern import (
    PatternDetection,
    PatternDirection,
    PatternReport,
    PatternResult,
    PatternType,
    StructureBreak,
)
from models.score import ComponentScore, ScoreModelOutput, ScoreReport, ScoreResult
from models.strategy import StrategyDirection, StrategyEvaluation, StrategyReport, StrategyResult

FROZEN_SAMPLES = [
    IndicatorOutput(name="ema"),
    IndicatorResult(),
    MarketResult(provider="x", status=MarketStatus.OK),
    PatternResult(
        name="fvg",
        pattern_type=PatternType.FAIR_VALUE_GAP,
        direction=PatternDirection.BULLISH,
        strength=1.0,
        confidence=0.5,
    ),
    PatternDetection(),
    PatternReport(),
    StructureBreak(0, datetime(2024, 1, 1, tzinfo=UTC), 1.0, PatternDirection.BULLISH, "bos"),
    StrategyResult(
        strategy_name="s",
        hypothesis_id="h",
        direction=StrategyDirection.BULLISH,
        confidence=0.5,
        strength=1.0,
    ),
    StrategyEvaluation(),
    StrategyReport(),
    ComponentScore("trend", 50.0, "reason"),
    ScoreModelOutput(name="m", value=1.0),
    ScoreResult(
        score_id="s",
        strategy_name="s",
        hypothesis_id="h",
        total_score=1.0,
        confidence=0.5,
        quality_score=1.0,
        consensus_score=1.0,
        market_score=1.0,
    ),
    ScoreReport(),
]


@pytest.mark.parametrize("obj", FROZEN_SAMPLES, ids=lambda o: type(o).__name__)
def test_result_models_are_frozen(obj: object) -> None:
    # Das Modell ist als frozen dataclass deklariert …
    assert type(obj).__dataclass_params__.frozen is True
    # … und verweigert zur Laufzeit jede Attribut-Zuweisung auf ein echtes Feld.
    first_field = dataclasses.fields(obj)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(obj, first_field, getattr(obj, first_field))
