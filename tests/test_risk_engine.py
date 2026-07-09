"""Tests für die Risk Engine (Orchestrierung, Validierung, Transparenz)."""

from __future__ import annotations

import pytest

from engines.risk_cache import RiskCache
from engines.risk_engine import RiskEngine, RiskRulesError, load_risk_rules
from models.risk import RISK_COMPONENT_NAMES, RiskLevel, RiskReport
from tests.helpers import (
    make_indicator_result,
    make_price_frame,
    make_score_report,
    make_score_result,
    make_settings,
)


def _engine(capital: float = 10000.0, cache: RiskCache | None = None, **settings_kwargs):
    return RiskEngine(
        rules=load_risk_rules(),
        settings=make_settings(capital=capital, **settings_kwargs),
        cache=cache,
    )


def _inputs(atr: float | None = 2.0, rows: int = 60, data=True):
    indicators = make_indicator_result(atr=atr, candle_count=rows)
    frame = make_price_frame([100.0 + i * 0.2 for i in range(rows)], volume=[1_000_000.0] * rows)
    return make_score_report(candle_count=rows), indicators, (frame if data else None)


# --- Grundfunktion -----------------------------------------------------------


def test_assess_returns_one_result_per_score() -> None:
    scores = [
        make_score_result(score_id="s1", hypothesis_id="h1"),
        make_score_result(score_id="s2", hypothesis_id="h2"),
    ]
    report = make_score_report(results=scores)
    _, indicators, data = _inputs()
    result = _engine().assess(report, indicators, data=data, symbol="AAPL")
    assert isinstance(result, RiskReport)
    assert result.risk_count == 2
    assert result.valid


def test_result_fields_populated() -> None:
    score_report, indicators, data = _inputs()
    r = _engine().assess(score_report, indicators, data=data).results[0]
    assert 0.0 <= r.overall_risk <= 100.0
    assert r.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH)
    assert set(r.risk_components) == set(RISK_COMPONENT_NAMES)
    assert r.estimated_shares > 0
    assert r.estimated_order_value > 0
    assert r.suggested_stop_distance == pytest.approx(4.0)
    assert r.suggested_risk_reward == 2.0
    assert r.risk_id == "risk:score:h1"
    assert r.hypothesis_id == "h1"


def test_transparency_reasons_present() -> None:
    score_report, indicators, data = _inputs()
    r = _engine().assess(score_report, indicators, data=data).results[0]
    for name in RISK_COMPONENT_NAMES:
        assert any(reason.startswith(f"{name}:") for reason in r.reasons), name


# --- Validierung -------------------------------------------------------------


def test_missing_scores_yields_warning() -> None:
    empty = make_score_report(results=[])
    _, indicators, data = _inputs()
    report = _engine().assess(empty, indicators, data=data)
    assert report.risk_count == 0
    assert any("Keine Scores" in w for w in report.warnings)


def test_negative_capital_invalid() -> None:
    score_report, indicators, data = _inputs()
    report = _engine(capital=-100.0).assess(score_report, indicators, data=data)
    assert report.valid is False
    assert report.risk_count == 0
    assert any("Depotgröße" in w for w in report.warnings)


def test_invalid_score_report_propagates() -> None:
    score_report = make_score_report(valid=False)
    _, indicators, data = _inputs()
    report = _engine().assess(score_report, indicators, data=data)
    assert report.valid is False


def test_missing_atr_flags_result() -> None:
    score_report, indicators, data = _inputs(atr=None)
    report = _engine().assess(score_report, indicators, data=data)
    assert report.valid is False
    r = report.results[0]
    assert r.estimated_shares == 0.0
    assert any("ATR" in w for w in r.warnings)


def test_missing_price_flags_result() -> None:
    score_report, indicators, _ = _inputs()
    report = _engine().assess(score_report, indicators, data=None)
    assert report.valid is False
    assert any("Preis" in w for w in report.results[0].warnings)


# --- Risikostufen ------------------------------------------------------------


def test_level_mapping() -> None:
    engine = _engine()
    assert engine._level(10.0) is RiskLevel.LOW
    assert engine._level(50.0) is RiskLevel.MEDIUM
    assert engine._level(80.0) is RiskLevel.HIGH


# --- Cache -------------------------------------------------------------------


def test_cache_returns_same_report() -> None:
    cache = RiskCache()
    engine = _engine(cache=cache)
    score_report, indicators, data = _inputs()
    first = engine.assess(score_report, indicators, data=data, symbol="AAPL")
    second = engine.assess(score_report, indicators, data=data, symbol="AAPL")
    assert first is second
    assert cache.hits == 1


# --- Registry als einzige Erweiterungsstelle ---------------------------------


def test_disabled_model_leaves_component_neutral(tmp_path) -> None:
    rules_text = (
        "[meta]\nversion = 9\n\n"
        "[overall]\nvolatility=0.1\nliquidity=0.1\ngap=0.1\nspread=0.1\natr=0.1\n"
        "market=0.1\ncorrelation=0.1\nportfolio_exposure=0.1\ndata_quality=0.1\nnews=0.1\n\n"
        "[levels]\nlow_max=33\nmedium_max=66\n\n"
        "[components]\natr_low_pct=1.0\natr_high_pct=6.0\nnews_default=50.0\n\n"
        "[position_sizing]\nenabled=true\natr_stop_multiplier=2.0\nrisk_reward=2.0\n"
        "slippage_bps=5.0\ncommission_pct=0.001\nmin_commission=1.0\nmax_position_pct=0.25\n"
        "max_portfolio_exposure_pct=1.0\n\n"
        "[volatility_risk]\nenabled=false\nwindow=20\nvol_low_pct=1.0\nvol_high_pct=5.0\n"
    )
    path = tmp_path / "risk_rules.toml"
    path.write_text(rules_text)
    engine = RiskEngine(rules=load_risk_rules(path), settings=make_settings())
    score_report, indicators, data = _inputs()
    r = engine.assess(score_report, indicators, data=data).results[0]
    # volatility-Modell deaktiviert -> Komponente neutral (50).
    assert r.risk_components["volatility"] == 50.0


def test_load_risk_rules_rejects_bad_weights(tmp_path) -> None:
    path = tmp_path / "bad.toml"
    path.write_text("[overall]\nvolatility=0.5\n")
    with pytest.raises(RiskRulesError):
        load_risk_rules(path)


def test_from_config_smoke() -> None:
    engine = RiskEngine.from_config()
    score_report, indicators, data = _inputs()
    report = engine.assess(score_report, indicators, data=data)
    assert report.valid
