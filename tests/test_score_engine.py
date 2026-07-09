"""Tests für die ScoreEngine (Bewertung, Validierung, Cache, Transparenz)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from engines.score_cache import ScoreCache
from engines.score_engine import ScoreEngine, ScoreRules, load_score_rules
from engines.score_registry import build_default_registry
from engines.strategy_result import StrategyReport
from scores.base import BaseScoreModel, ScoreContext, ScoreModelOutput
from strategies.base import StrategyDirection
from tests.helpers import (
    make_indicator_result,
    make_pattern_report,
    make_pattern_result,
    make_strategy_result,
)


def _indicators():
    return make_indicator_result(
        ema={20: 110, 50: 105, 200: 100},
        adx=30.0,
        rsi=60.0,
        macd={"macd": 1.0, "signal": 0.0, "histogram": 0.5},
        relative_volume=2.0,
        bollinger={"upper": 120.0, "middle": 100.0, "lower": 90.0},
    )


def _patterns():
    return make_pattern_report([make_pattern_result("fvg", strength=80.0, confidence=0.9)])


def _strategy_report(count: int = 2, direction: StrategyDirection = StrategyDirection.BULLISH):
    results = [
        make_strategy_result(strategy_name=f"strat{i}", direction=direction, confidence=0.7)
        for i in range(count)
    ]
    return StrategyReport(results=results, metadata={"timeframe": "base", "candle_count": 260})


def _engine(cache: ScoreCache | None = None) -> ScoreEngine:
    return ScoreEngine(load_score_rules(), cache=cache)


def test_scores_one_result_per_hypothesis() -> None:
    report = _engine().score(_strategy_report(3), _indicators(), _patterns(), symbol="TEST")
    assert report.valid is True
    assert report.score_count == 3


def test_named_fields_populated() -> None:
    report = _engine().score(_strategy_report(1), _indicators(), _patterns())
    result = report.results[0]
    assert result.total_score > 0
    assert 0.0 <= result.confidence <= 1.0
    assert result.quality_score > 0
    assert result.consensus_score == 100.0  # alle gleiche Richtung
    assert result.market_score > 0


def test_all_eight_components_stored() -> None:
    report = _engine().score(_strategy_report(1), _indicators(), _patterns())
    components = report.results[0].component_scores
    assert set(components) == {
        "trend",
        "momentum",
        "pattern_strength",
        "pattern_confidence",
        "indicator_quality",
        "market_context",
        "volume_quality",
        "data_quality",
    }


def test_transparent_breakdown_in_reasons() -> None:
    report = _engine().score(_strategy_report(1), _indicators(), _patterns())
    reasons = report.results[0].reasons
    assert any(r.startswith("[weighted_score] trend:") for r in reasons)


def test_model_scores_in_metadata() -> None:
    report = _engine().score(_strategy_report(1), _indicators(), _patterns())
    model_scores = report.results[0].metadata["model_scores"]
    assert set(model_scores) == {
        "weighted_score",
        "confidence_score",
        "quality_score",
        "consensus_score",
        "market_score",
    }


def test_score_id_format() -> None:
    report = _engine().score(_strategy_report(1), _indicators(), _patterns())
    result = report.results[0]
    assert result.score_id == f"score:{result.hypothesis_id}"


def test_no_hypotheses_warns() -> None:
    report = _engine().score(StrategyReport(results=[]), _indicators(), _patterns())
    assert report.score_count == 0
    assert any("Keine Hypothesen" in w for w in report.warnings)


def test_invalid_strategy_report_marks_invalid() -> None:
    report = _engine().score(
        StrategyReport(results=[make_strategy_result()], valid=False), _indicators(), _patterns()
    )
    assert report.valid is False
    assert any("Strategie-Report" in w for w in report.warnings)


def test_invalid_weights_mark_invalid() -> None:
    rules = ScoreRules(
        models={"weighted_score": {"enabled": True, "trend": 0.9, "momentum": 0.9}}, version=1
    )
    report = ScoreEngine(rules).score(_strategy_report(1), _indicators(), _patterns())
    assert report.valid is False
    result = report.results[0]
    assert result.total_score == 0.0
    assert any("100" in w or "fehlende" in w for w in result.warnings)


def test_cache_used() -> None:
    cache = ScoreCache()
    engine = _engine(cache=cache)
    strat, ind, pat = _strategy_report(2), _indicators(), _patterns()
    engine.score(strat, ind, pat, symbol="X")
    engine.score(strat, ind, pat, symbol="X")
    assert cache.hits == 1
    assert cache.misses == 1


def test_top_sorts_by_total_score() -> None:
    report = _engine().score(_strategy_report(3), _indicators(), _patterns())
    top = report.top(2)
    assert len(top) == 2
    assert top[0].total_score >= top[1].total_score


def test_metadata_scored_count() -> None:
    report = _engine().score(_strategy_report(2), _indicators(), _patterns())
    assert report.metadata["scored"] == 2


def test_new_model_runs_without_engine_change() -> None:
    class DummyModel(BaseScoreModel):
        name = "dummy"

        def compute(self, context: ScoreContext, params: Mapping[str, Any]) -> ScoreModelOutput:
            return ScoreModelOutput(name=self.name, value=42.0, reasons=["dummy reason"])

    registry = build_default_registry()
    registry.register(DummyModel())
    rules = ScoreRules(models={"dummy": {"enabled": True}}, version=1)
    report = ScoreEngine(rules, registry=registry).score(
        _strategy_report(1), _indicators(), _patterns()
    )
    assert report.results[0].metadata["model_scores"]["dummy"] == 42.0
