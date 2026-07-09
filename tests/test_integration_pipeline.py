"""End-to-End-Integrationstests der vollständigen AlphaAI-Pipeline.

Kein Mock: jeder Test lässt echte Marktszenarien durch die **echte** Kette
``IndicatorEngine → PatternEngine → StrategyEngine → ScoreEngine → RiskEngine
→ RecommendationEngine`` laufen und prüft Struktur, Konsistenz und die
zentralen Entscheidungs-Invarianten.
"""

from __future__ import annotations

import dataclasses

import pytest

import tests.scenarios as scenarios
from models.pipeline import PipelineResult
from models.recommendation import RecommendationLevel, SuggestedAction
from models.risk import RISK_COMPONENT_NAMES
from pipeline.consistency import verify_pipeline
from pipeline.runner import IntegrationRunner

SCENARIO_NAMES = sorted(scenarios.SCENARIOS)

# Gate-Schwellen (spiegeln knowledge/recommendation_rules.toml) für Invarianten.
MIN_CONSENSUS_FOR_BUY = 60.0
MIN_DATA_QUALITY = 60.0
MAX_RISK_FOR_BUY = 66.0
BUY_LEVELS = (RecommendationLevel.STRONG_BUY, RecommendationLevel.BUY)


@pytest.fixture(scope="module")
def runner() -> IntegrationRunner:
    return IntegrationRunner.from_config()


@pytest.fixture(scope="module")
def results(runner: IntegrationRunner) -> dict[str, PipelineResult]:
    """Führt jedes Szenario **einmal** durch die komplette Pipeline."""
    out: dict[str, PipelineResult] = {}
    for name in SCENARIO_NAMES:
        frame = scenarios.SCENARIOS[name]()
        out[name] = runner.run_frame(frame, symbol=name[:8].upper())
    return out


# --------------------------------------------------------------------------- #
# Parametrisierte Struktur-/Konsistenz-Prüfungen (je Szenario)                #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_pipeline_completes(results, name: str) -> None:
    r = results[name]
    assert isinstance(r, PipelineResult)
    assert r.symbol == name[:8].upper()


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_all_reports_present(results, name: str) -> None:
    r = results[name]
    assert r.indicators is not None
    assert r.patterns is not None
    assert r.strategies is not None
    assert r.scores is not None
    assert r.risks is not None
    assert r.recommendations is not None


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_consistency_zero_violations(results, name: str) -> None:
    assert verify_pipeline(results[name]) == []


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_stage_counts_aligned(results, name: str) -> None:
    r = results[name]
    # Jeder Score hat genau eine Strategie, jedes Risk genau einen Score,
    # jede Empfehlung genau ein Risk.
    assert r.scores.score_count == r.strategies.hypothesis_count
    assert r.risks.risk_count == r.scores.score_count
    assert r.recommendations.recommendation_count == r.risks.risk_count


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_recommendation_levels_and_actions_valid(results, name: str) -> None:
    for rec in results[name].recommendations.results:
        assert rec.recommendation_level in RecommendationLevel
        assert rec.suggested_action in SuggestedAction


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_rating_and_confidence_in_range(results, name: str) -> None:
    for rec in results[name].recommendations.results:
        assert 0.0 <= rec.overall_rating <= 100.0
        assert 0.0 <= rec.confidence <= 1.0


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_recommendation_ids_unique(results, name: str) -> None:
    ids = [rec.recommendation_id for rec in results[name].recommendations.results]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_each_recommendation_fully_referenced(results, name: str) -> None:
    r = results[name]
    strat_ids = {s.hypothesis_id for s in r.strategies.results}
    score_ids = {s.score_id for s in r.scores.results}
    risk_ids = {rk.risk_id for rk in r.risks.results}
    for rec in r.recommendations.results:
        assert rec.hypothesis_id in strat_ids
        assert rec.score_id in score_ids
        assert rec.risk_id in risk_ids


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_risk_components_complete(results, name: str) -> None:
    for risk in results[name].risks.results:
        assert set(risk.risk_components) == set(RISK_COMPONENT_NAMES)


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_recommendations_are_explainable(results, name: str) -> None:
    for rec in results[name].recommendations.results:
        assert rec.reasons, "Empfehlung ohne Reasons (Blackbox unzulässig)."
        assert rec.summary
        assert rec.summary.startswith(rec.recommendation_level.value.upper())


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_scores_in_range(results, name: str) -> None:
    for score in results[name].scores.results:
        assert 0.0 <= score.total_score <= 100.0


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_pipeline_result_is_frozen(results, name: str) -> None:
    r = results[name]
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.symbol = "X"  # type: ignore[misc]


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_no_action_without_recommendation(results, name: str) -> None:
    # Struktur-Invariante: Handlung folgt immer aus der Stufe.
    for rec in results[name].recommendations.results:
        if rec.recommendation_level in BUY_LEVELS:
            assert rec.suggested_action is SuggestedAction.OPEN
        elif rec.recommendation_level is RecommendationLevel.WATCH:
            assert rec.suggested_action is SuggestedAction.MONITOR
        elif rec.recommendation_level is RecommendationLevel.WAIT:
            assert rec.suggested_action is SuggestedAction.WAIT
        else:
            assert rec.suggested_action is SuggestedAction.SKIP


# --------------------------------------------------------------------------- #
# Zentrale Entscheidungs-Invarianten (über alle Szenarien)                    #
# --------------------------------------------------------------------------- #


def _all_recs(results):
    for name in SCENARIO_NAMES:
        r = results[name]
        risk_by_hyp = {rk.hypothesis_id: rk for rk in r.risks.results}
        for rec in r.recommendations.results:
            yield name, rec, risk_by_hyp.get(rec.hypothesis_id)


def test_high_risk_never_buy(results) -> None:
    """Hohes Risiko deckelt die Empfehlung – nie BUY/STRONG_BUY bei Risiko > Cap."""
    for name, rec, risk in _all_recs(results):
        if risk is not None and risk.overall_risk > MAX_RISK_FOR_BUY:
            assert rec.recommendation_level not in BUY_LEVELS, name


def test_buy_requires_all_gates(results) -> None:
    """BUY/STRONG_BUY nur, wenn Konsens, Datenqualität und Risiko die Gates erfüllen."""
    for name, rec, risk in _all_recs(results):
        if rec.recommendation_level in BUY_LEVELS:
            factors = rec.metadata["factors"]
            assert factors["consensus"] >= MIN_CONSENSUS_FOR_BUY, name
            assert factors["data_quality"] >= MIN_DATA_QUALITY, name
            assert risk is not None and risk.overall_risk <= MAX_RISK_FOR_BUY, name


def test_score_alone_never_buy(results) -> None:
    """Ein hoher Score allein (ohne Konsens) erzeugt nie BUY."""
    for name, rec, _ in _all_recs(results):
        score = rec.metadata["factors"]["score"]
        consensus = rec.metadata["factors"]["consensus"]
        if score >= 80.0 and consensus < MIN_CONSENSUS_FOR_BUY:
            assert rec.recommendation_level not in BUY_LEVELS, name


def test_no_trade_is_a_normal_outcome(results) -> None:
    """WAIT/AVOID kommen als vollwertige Empfehlungen vor."""
    levels = [rec.recommendation_level for _, rec, _ in _all_recs(results)]
    no_trade = {RecommendationLevel.WAIT, RecommendationLevel.AVOID, RecommendationLevel.WATCH}
    assert any(level in no_trade for level in levels)


def test_strong_buy_is_not_universal(results) -> None:
    """STRONG_BUY ist außergewöhnlich – nicht jedes Szenario liefert es."""
    levels = [rec.recommendation_level for _, rec, _ in _all_recs(results)]
    strong = sum(1 for level in levels if level is RecommendationLevel.STRONG_BUY)
    assert strong < len(levels) if levels else True


# --------------------------------------------------------------------------- #
# Gezielte Szenario-Fälle                                                     #
# --------------------------------------------------------------------------- #


def test_missing_data_produces_no_recommendations(runner: IntegrationRunner) -> None:
    from models.market import MarketResult, MarketStatus

    result = runner.run(MarketResult(provider="x", status=MarketStatus.EMPTY), "NONE")
    assert result.recommendation_count == 0
    assert verify_pipeline(result) == []
    assert result.metadata["all_stages_valid"] is False


def test_short_history_no_buy(runner: IntegrationRunner) -> None:
    result = runner.run_frame(scenarios.short_history(), symbol="SHORT")
    assert verify_pipeline(result) == []
    for rec in result.recommendations.results:
        assert rec.recommendation_level not in BUY_LEVELS


def test_low_liquidity_raises_risk_vs_high(runner: IntegrationRunner) -> None:
    low = runner.run_frame(scenarios.low_liquidity(), symbol="LOWLIQ")
    high = runner.run_frame(scenarios.high_liquidity(), symbol="HIGHLIQ")
    low_liq = [r.risk_components["liquidity"] for r in low.risks.results]
    high_liq = [r.risk_components["liquidity"] for r in high.risks.results]
    if low_liq and high_liq:
        assert max(low_liq) >= max(high_liq)


def test_high_volatility_raises_risk_vs_low(runner: IntegrationRunner) -> None:
    hv = runner.run_frame(scenarios.high_volatility(), symbol="HIVOL")
    lv = runner.run_frame(scenarios.low_volatility(), symbol="LOVOL")
    hv_vol = [r.risk_components["volatility"] for r in hv.risks.results]
    lv_vol = [r.risk_components["volatility"] for r in lv.risks.results]
    if hv_vol and lv_vol:
        assert max(hv_vol) >= max(lv_vol)


def test_run_all_covers_all_symbols(runner: IntegrationRunner) -> None:
    from models.market import MarketResult, MarketStatus

    market = MarketResult(
        provider="synthetic",
        status=MarketStatus.OK,
        data={"AAA": scenarios.trend_up(), "BBB": scenarios.trend_down()},
    )
    out = runner.run_all(market)
    assert set(out) == {"AAA", "BBB"}
    for result in out.values():
        assert verify_pipeline(result) == []


def test_from_config_builds_full_runner() -> None:
    runner = IntegrationRunner.from_config()
    result = runner.run_frame(scenarios.trend_up(), symbol="CFG")
    assert result.recommendation_count == result.risks.risk_count
