"""Tests für die Recommendation Engine (Logik, Validierung, No-Trade, Transparenz)."""

from __future__ import annotations

import pytest

from engines.recommendation_cache import RecommendationCache
from engines.recommendation_engine import (
    RecommendationEngine,
    RecommendationRulesError,
    load_recommendation_rules,
)
from engines.strategy_result import StrategyReport
from models.recommendation import RecommendationLevel, RecommendationReport, SuggestedAction
from models.risk import RiskLevel
from models.score import ScoreReport
from tests.helpers import (
    make_risk_report,
    make_risk_result,
    make_score_report,
    make_score_result,
    make_strategy_result,
)


def _engine(cache: RecommendationCache | None = None) -> RecommendationEngine:
    return RecommendationEngine(rules=load_recommendation_rules(), cache=cache)


def _reports(
    n: int = 2,
    total: float = 91.0,
    market: float = 70.0,
    risk_overall: float = 20.0,
    risk_level: RiskLevel = RiskLevel.LOW,
    data_quality: float = 100.0,
    direction=None,
):
    strategies, scores, risks = [], [], []
    for i in range(1, n + 1):
        hyp = f"h{i}"
        strategies.append(
            make_strategy_result(
                hypothesis_id=hyp, strength=70.0, confidence=0.7, direction=direction
            )
        )
        scores.append(
            make_score_result(
                score_id=f"score:{hyp}",
                hypothesis_id=hyp,
                total_score=total,
                market_score=market,
                data_quality=data_quality,
            )
        )
        risks.append(
            make_risk_result(hypothesis_id=hyp, overall_risk=risk_overall, risk_level=risk_level)
        )
    return (
        StrategyReport(results=strategies, valid=True),
        ScoreReport(results=scores, valid=True),
        make_risk_report(results=risks, valid=True),
    )


# --- Grundfunktion -----------------------------------------------------------


def test_recommend_one_result_per_score() -> None:
    sr, sc, rk = _reports(n=2)
    report = _engine().recommend(sr, sc, rk, symbol="AAPL")
    assert isinstance(report, RecommendationReport)
    assert report.recommendation_count == 2
    assert report.valid


def test_result_fields_populated() -> None:
    sr, sc, rk = _reports(n=2)
    r = _engine().recommend(sr, sc, rk, symbol="AAPL").results[0]
    assert r.recommendation_level in RecommendationLevel
    assert r.suggested_action in SuggestedAction
    assert 0.0 <= r.confidence <= 1.0
    assert 0.0 <= r.overall_rating <= 100.0
    assert r.recommendation_id == "rec:score:h1"
    assert r.risk_id == "risk:score:h1"
    assert r.score_id == "score:h1"
    assert r.hypothesis_id == "h1"
    assert r.summary
    assert r.reasons


# --- Entscheidungslogik ------------------------------------------------------


def test_two_confirming_strong_or_buy() -> None:
    sr, sc, rk = _reports(n=2, total=95, market=80)
    r = _engine().recommend(sr, sc, rk).results[0]
    assert r.recommendation_level in (RecommendationLevel.STRONG_BUY, RecommendationLevel.BUY)
    assert r.suggested_action is SuggestedAction.OPEN


def test_single_strategy_high_score_not_buy() -> None:
    sr, sc, rk = _reports(n=1, total=99, market=95)
    r = _engine().recommend(sr, sc, rk).results[0]
    # Hoher Score allein -> nie BUY/STRONG_BUY.
    assert r.recommendation_level not in (RecommendationLevel.STRONG_BUY, RecommendationLevel.BUY)


def test_high_risk_caps_recommendation() -> None:
    sr, sc, rk = _reports(n=2, total=95, market=80, risk_overall=85, risk_level=RiskLevel.HIGH)
    r = _engine().recommend(sr, sc, rk).results[0]
    assert r.recommendation_level not in (RecommendationLevel.STRONG_BUY, RecommendationLevel.BUY)


def test_low_data_quality_reduces() -> None:
    sr, sc, rk = _reports(n=2, total=95, market=80, data_quality=20)
    r = _engine().recommend(sr, sc, rk).results[0]
    assert r.recommendation_level in (RecommendationLevel.WAIT, RecommendationLevel.AVOID)


def test_weak_setup_yields_no_trade() -> None:
    sr, sc, rk = _reports(
        n=1, total=10, market=10, risk_overall=90, risk_level=RiskLevel.HIGH, data_quality=20
    )
    r = _engine().recommend(sr, sc, rk).results[0]
    assert r.recommendation_level in (RecommendationLevel.WAIT, RecommendationLevel.AVOID)
    assert r.suggested_action in (SuggestedAction.WAIT, SuggestedAction.SKIP)


# --- Transparenz -------------------------------------------------------------


def test_summary_starts_with_level() -> None:
    sr, sc, rk = _reports(n=2, total=95, market=80)
    r = _engine().recommend(sr, sc, rk).results[0]
    assert r.summary.startswith(r.recommendation_level.value.upper())


def test_reasons_include_gate_explanation() -> None:
    sr, sc, rk = _reports(n=1, total=99, market=95)
    r = _engine().recommend(sr, sc, rk).results[0]
    assert any("Konsens" in reason for reason in r.reasons)


def test_metadata_has_factors() -> None:
    sr, sc, rk = _reports(n=2)
    r = _engine().recommend(sr, sc, rk).results[0]
    assert set(r.metadata["factors"]) >= {"strategy", "score", "risk", "consensus"}


# --- Validierung -------------------------------------------------------------


def test_invalid_strategy_report_propagates() -> None:
    sr, sc, rk = _reports(n=1)
    sr = StrategyReport(results=sr.results, valid=False)
    report = _engine().recommend(sr, sc, rk)
    assert report.valid is False
    assert any("Strategie" in w for w in report.warnings)


def test_invalid_score_report_propagates() -> None:
    sr, sc, rk = _reports(n=1)
    sc = ScoreReport(results=sc.results, valid=False)
    report = _engine().recommend(sr, sc, rk)
    assert report.valid is False


def test_invalid_risk_report_propagates() -> None:
    sr, sc, rk = _reports(n=1)
    report = _engine().recommend(sr, sc, make_risk_report(results=rk.results, valid=False))
    assert report.valid is False


def test_missing_scores_yields_warning() -> None:
    sr, _, rk = _reports(n=1)
    report = _engine().recommend(sr, make_score_report(results=[]), rk)
    assert report.recommendation_count == 0
    assert any("Keine Scores" in w for w in report.warnings)


def test_missing_strategy_or_risk_skips_with_warning() -> None:
    sr, sc, _ = _reports(n=1)
    # Risiko-Report ohne passende Hypothese.
    other_risk = make_risk_report(results=[make_risk_result(hypothesis_id="other")])
    report = _engine().recommend(sr, sc, other_risk)
    assert report.valid is False
    assert report.recommendation_count == 0
    assert any("Fehlende Strategie-/Risiko-Daten" in w for w in report.warnings)


# --- Cache -------------------------------------------------------------------


def test_cache_returns_same_report() -> None:
    cache = RecommendationCache()
    engine = _engine(cache=cache)
    sr, sc, rk = _reports(n=2)
    first = engine.recommend(sr, sc, rk, symbol="AAPL")
    second = engine.recommend(sr, sc, rk, symbol="AAPL")
    assert first is second
    assert cache.hits == 1


# --- Registry / Config -------------------------------------------------------


def test_disabled_recommendation_model_falls_back_to_wait(tmp_path) -> None:
    rules_text = (
        "[meta]\nversion=9\n\n"
        "[weights]\nstrategy=0.15\nscore=0.25\nrisk=0.20\nconsensus=0.20\n"
        "market_quality=0.10\ndata_quality=0.10\n\n"
        "[factors]\nconsensus_full_at=2\n\n"
        "[confidence]\nstrategy_confidence=0.35\nconsensus=0.30\nrisk=0.20\ndata_quality=0.15\n\n"
        "[decision_model]\nenabled=true\n\n"
        "[recommendation_model]\nenabled=false\n"
    )
    path = tmp_path / "rec.toml"
    path.write_text(rules_text)
    engine = RecommendationEngine(rules=load_recommendation_rules(path))
    sr, sc, rk = _reports(n=2, total=95, market=80)
    r = engine.recommend(sr, sc, rk).results[0]
    assert r.recommendation_level is RecommendationLevel.WAIT


def test_load_rules_rejects_bad_weights(tmp_path) -> None:
    path = tmp_path / "bad.toml"
    path.write_text("[weights]\nstrategy=0.5\n[confidence]\nrisk=1.0\n[m]\nenabled=true\n")
    with pytest.raises(RecommendationRulesError):
        load_recommendation_rules(path)


def test_from_config_smoke() -> None:
    engine = RecommendationEngine.from_config()
    sr, sc, rk = _reports(n=2)
    assert engine.recommend(sr, sc, rk).valid
