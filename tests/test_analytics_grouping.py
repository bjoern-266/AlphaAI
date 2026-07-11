"""Tests für die gruppierenden Analysen (Strategie/Recommendation/Risk/Pattern/Markt)."""

from __future__ import annotations

from analytics.market_analysis import MarketAnalysisModel
from analytics.pattern_analysis import PatternAnalysisModel
from analytics.recommendation_analysis import RecommendationAnalysisModel
from analytics.risk_analysis import RiskAnalysisModel
from analytics.strategy_analysis import StrategyAnalysisModel
from models.recommendation import RecommendationStrength
from tests.helpers import make_analytics_context, make_analytics_trade


# --- Strategy ---------------------------------------------------------------
def test_strategy_groups():
    trades = [
        make_analytics_trade(strategy="trend_following", pnl=100.0),
        make_analytics_trade(strategy="momentum", pnl=-20.0),
        make_analytics_trade(strategy="trend_following", pnl=50.0),
    ]
    out = StrategyAnalysisModel().compute(make_analytics_context(trades=trades), {})
    stats = out.statistics["strategy"]
    assert set(stats) == {"trend_following", "momentum"}
    assert stats["trend_following"].trade_count == 2
    assert stats["momentum"].loss_rate == 1.0


def test_strategy_metric_count():
    out = StrategyAnalysisModel().compute(make_analytics_context(), {})
    assert out.metrics["strategy_count"] == 1.0


# --- Recommendation ---------------------------------------------------------
def test_recommendation_groups_by_strength():
    trades = [
        make_analytics_trade(strength=RecommendationStrength.VERY_HIGH, pnl=100.0),
        make_analytics_trade(strength=RecommendationStrength.MEDIUM, pnl=-10.0),
    ]
    out = RecommendationAnalysisModel().compute(make_analytics_context(trades=trades), {})
    stats = out.statistics["recommendation_strength"]
    assert set(stats) == {"very_high", "medium"}


def test_recommendation_average_return_in_group():
    trades = [
        make_analytics_trade(strength=RecommendationStrength.HIGH, pnl=100.0),
        make_analytics_trade(strength=RecommendationStrength.HIGH, pnl=-40.0),
    ]
    out = RecommendationAnalysisModel().compute(make_analytics_context(trades=trades), {})
    assert out.statistics["recommendation_strength"]["high"].average_return == 30.0


# --- Risk -------------------------------------------------------------------
def test_risk_groups_by_level():
    trades = [
        make_analytics_trade(risk_level="low", pnl=50.0),
        make_analytics_trade(risk_level="high", pnl=-80.0),
    ]
    out = RiskAnalysisModel().compute(make_analytics_context(trades=trades), {})
    stats = out.statistics["risk_level"]
    assert set(stats) == {"low", "high"}
    assert stats["high"].average_loser == -80.0


def test_risk_unknown_warns():
    trades = [make_analytics_trade(risk_level="unbekannt")]
    out = RiskAnalysisModel().compute(make_analytics_context(trades=trades), {})
    assert out.warnings


# --- Pattern ----------------------------------------------------------------
def test_pattern_groups_by_label():
    trades = [
        make_analytics_trade(labels={"pattern": "fvg"}, pnl=100.0),
        make_analytics_trade(labels={"pattern": "bos"}, pnl=-10.0),
    ]
    out = PatternAnalysisModel().compute(make_analytics_context(trades=trades), {})
    stats = out.statistics["pattern"]
    assert set(stats) == {"fvg", "bos"}


def test_pattern_unknown_warns():
    trades = [make_analytics_trade(labels={})]
    out = PatternAnalysisModel().compute(make_analytics_context(trades=trades), {})
    assert set(out.statistics["pattern"]) == {"unbekannt"}
    assert out.warnings


# --- Market -----------------------------------------------------------------
def test_market_dimensions_present():
    out = MarketAnalysisModel().compute(make_analytics_context(), {})
    assert set(out.statistics) == {"market_phase", "volatility", "liquidity"}


def test_market_uses_labels_when_present():
    trades = [
        make_analytics_trade(labels={"market_phase": "trend"}, pnl=100.0),
        make_analytics_trade(labels={"market_phase": "sideways"}, pnl=-10.0),
    ]
    out = MarketAnalysisModel().compute(make_analytics_context(trades=trades), {})
    assert set(out.statistics["market_phase"]) == {"trend", "sideways"}


def test_market_unknown_warns():
    out = MarketAnalysisModel().compute(make_analytics_context(), {})
    assert out.warnings


def test_strategy_group_has_holding_and_drawdown():
    trades = [
        make_analytics_trade(strategy="s", pnl=100.0, holding_days=4.0),
        make_analytics_trade(strategy="s", pnl=-60.0, holding_days=2.0),
    ]
    stat = (
        StrategyAnalysisModel()
        .compute(make_analytics_context(trades=trades), {})
        .statistics["strategy"]["s"]
    )
    assert stat.average_holding_time == 3.0
    assert stat.maximum_drawdown >= 0.0


def test_recommendation_trade_count_per_group():
    trades = [
        make_analytics_trade(strength=RecommendationStrength.LOW, pnl=10.0),
        make_analytics_trade(strength=RecommendationStrength.LOW, pnl=-5.0),
        make_analytics_trade(strength=RecommendationStrength.HIGH, pnl=20.0),
    ]
    stats = (
        RecommendationAnalysisModel()
        .compute(make_analytics_context(trades=trades), {})
        .statistics["recommendation_strength"]
    )
    assert stats["low"].trade_count == 2
    assert stats["high"].trade_count == 1


def test_risk_group_profit_factor():
    trades = [
        make_analytics_trade(risk_level="low", pnl=100.0),
        make_analytics_trade(risk_level="low", pnl=-50.0),
    ]
    stat = (
        RiskAnalysisModel()
        .compute(make_analytics_context(trades=trades), {})
        .statistics["risk_level"]["low"]
    )
    assert stat.profit_factor == 2.0


def test_market_volatility_and_liquidity_labels():
    trades = [
        make_analytics_trade(labels={"volatility": "high", "liquidity": "low"}, pnl=10.0),
    ]
    out = MarketAnalysisModel().compute(make_analytics_context(trades=trades), {})
    assert "high" in out.statistics["volatility"]
    assert "low" in out.statistics["liquidity"]


def test_empty_context_grouping_returns_empty():
    out = StrategyAnalysisModel().compute(make_analytics_context(trades=[]), {})
    assert out.statistics["strategy"] == {}
