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
from models.recommendation import Direction, RecommendationStrength, SuggestedAction
from models.risk import RISK_COMPONENT_NAMES
from pipeline.consistency import verify_pipeline
from pipeline.runner import IntegrationRunner

SCENARIO_NAMES = sorted(scenarios.SCENARIOS)

# Gate-Schwellen (spiegeln knowledge/recommendation_rules.toml) für Invarianten.
MIN_CONSENSUS_FOR_HIGH = 60.0
MIN_DATA_QUALITY = 60.0
MAX_RISK_FOR_HIGH = 66.0
# Hohe Empfehlungsstärke (entspricht früher BUY/STRONG_BUY, ohne Richtungsbezug).
HIGH_STRENGTHS = (RecommendationStrength.VERY_HIGH, RecommendationStrength.HIGH)


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
def test_recommendation_strength_direction_and_actions_valid(results, name: str) -> None:
    for rec in results[name].recommendations.results:
        assert rec.recommendation_strength in RecommendationStrength
        assert rec.direction in Direction
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
        assert rec.summary.startswith(rec.direction.value.upper())


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
def test_action_follows_strength(results, name: str) -> None:
    # Struktur-Invariante: Handlung folgt immer aus der Stärke.
    for rec in results[name].recommendations.results:
        if rec.recommendation_strength in HIGH_STRENGTHS:
            assert rec.suggested_action is SuggestedAction.OPEN
        elif rec.recommendation_strength is RecommendationStrength.MEDIUM:
            assert rec.suggested_action is SuggestedAction.MONITOR
        elif rec.recommendation_strength is RecommendationStrength.LOW:
            assert rec.suggested_action is SuggestedAction.WAIT
        else:
            assert rec.suggested_action is SuggestedAction.SKIP


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_direction_matches_strategy(results, name: str) -> None:
    # Fachliche Trennung: die Richtung folgt der Strategie-Hypothese.
    from models.strategy import StrategyDirection

    mapping = {
        StrategyDirection.BULLISH: Direction.LONG,
        StrategyDirection.BEARISH: Direction.SHORT,
        StrategyDirection.NEUTRAL: Direction.NEUTRAL,
    }
    r = results[name]
    strat_by_hyp = {s.hypothesis_id: s for s in r.strategies.results}
    for rec in r.recommendations.results:
        strat = strat_by_hyp[rec.hypothesis_id]
        assert rec.direction is mapping[strat.direction]


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_strength_never_contains_direction_terms(results, name: str) -> None:
    # Die Stärke darf niemals BUY/SELL/LONG/SHORT implizieren.
    forbidden = {"buy", "sell", "long", "short", "strong_buy"}
    for rec in results[name].recommendations.results:
        assert rec.recommendation_strength.value not in forbidden


# --------------------------------------------------------------------------- #
# Zentrale Entscheidungs-Invarianten (über alle Szenarien)                    #
# --------------------------------------------------------------------------- #


def _all_recs(results):
    for name in SCENARIO_NAMES:
        r = results[name]
        risk_by_hyp = {rk.hypothesis_id: rk for rk in r.risks.results}
        for rec in r.recommendations.results:
            yield name, rec, risk_by_hyp.get(rec.hypothesis_id)


def test_high_risk_never_high_strength(results) -> None:
    """Hohes Risiko deckelt – nie HIGH/VERY_HIGH bei Risiko > Cap."""
    for name, rec, risk in _all_recs(results):
        if risk is not None and risk.overall_risk > MAX_RISK_FOR_HIGH:
            assert rec.recommendation_strength not in HIGH_STRENGTHS, name


def test_high_strength_requires_all_gates(results) -> None:
    """HIGH/VERY_HIGH nur, wenn Konsens, Datenqualität und Risiko die Gates erfüllen."""
    for name, rec, risk in _all_recs(results):
        if rec.recommendation_strength in HIGH_STRENGTHS:
            factors = rec.metadata["factors"]
            assert factors["consensus"] >= MIN_CONSENSUS_FOR_HIGH, name
            assert factors["data_quality"] >= MIN_DATA_QUALITY, name
            assert risk is not None and risk.overall_risk <= MAX_RISK_FOR_HIGH, name


def test_score_alone_never_high_strength(results) -> None:
    """Ein hoher Score allein (ohne Konsens) erzeugt nie HIGH/VERY_HIGH."""
    for name, rec, _ in _all_recs(results):
        score = rec.metadata["factors"]["score"]
        consensus = rec.metadata["factors"]["consensus"]
        if score >= 80.0 and consensus < MIN_CONSENSUS_FOR_HIGH:
            assert rec.recommendation_strength not in HIGH_STRENGTHS, name


def test_bearish_scenarios_are_short_not_buy(results) -> None:
    """Der 9.5-Befund ist behoben: bärische Setups sind SHORT, nie „BUY"."""
    forbidden = {"buy", "sell", "long", "short", "strong_buy"}
    saw_short = False
    for _name, rec, _risk in _all_recs(results):
        if rec.direction is Direction.SHORT:
            saw_short = True
            # Ein bärisches Setup wird nie als Kauf dargestellt.
            assert rec.recommendation_strength.value not in forbidden
    # Mindestens ein bärisches Setup trat auf (trend_down/breakout_down).
    assert saw_short


def test_no_trade_is_a_normal_outcome(results) -> None:
    """MEDIUM/LOW/REJECT kommen als vollwertige Empfehlungen vor."""
    strengths = [rec.recommendation_strength for _, rec, _ in _all_recs(results)]
    no_trade = {
        RecommendationStrength.MEDIUM,
        RecommendationStrength.LOW,
        RecommendationStrength.REJECT,
    }
    assert any(strength in no_trade for strength in strengths)


def test_very_high_is_not_universal(results) -> None:
    """VERY_HIGH ist außergewöhnlich – nicht jede Empfehlung erreicht es."""
    strengths = [rec.recommendation_strength for _, rec, _ in _all_recs(results)]
    very_high = sum(1 for s in strengths if s is RecommendationStrength.VERY_HIGH)
    assert very_high < len(strengths) if strengths else True


# --------------------------------------------------------------------------- #
# Gezielte Szenario-Fälle                                                     #
# --------------------------------------------------------------------------- #


def test_missing_data_produces_no_recommendations(runner: IntegrationRunner) -> None:
    from models.market import MarketResult, MarketStatus

    result = runner.run(MarketResult(provider="x", status=MarketStatus.EMPTY), "NONE")
    assert result.recommendation_count == 0
    assert verify_pipeline(result) == []
    assert result.metadata["all_stages_valid"] is False


def test_short_history_no_high_strength(runner: IntegrationRunner) -> None:
    result = runner.run_frame(scenarios.short_history(), symbol="SHORT")
    assert verify_pipeline(result) == []
    for rec in result.recommendations.results:
        assert rec.recommendation_strength not in HIGH_STRENGTHS


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
