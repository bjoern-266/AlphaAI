"""Tests für die Dimensions-Ableitung (analytics.labeling)."""

from __future__ import annotations

from analytics import labeling as lab


def test_parse_strategy_standard():
    rid = "rec:score:trend_following:bullish:AAPL:2023-01-02T00:00:00"
    assert lab.parse_strategy(rid) == "trend_following"


def test_parse_strategy_score_prefix():
    assert lab.parse_strategy("score:momentum:bearish:XY:t") == "momentum"


def test_parse_strategy_empty():
    assert lab.parse_strategy("") == lab.UNKNOWN


def test_parse_strategy_unknown_format():
    assert lab.parse_strategy("weird-id") == lab.UNKNOWN


def test_parse_risk_level_word():
    assert lab.parse_risk_level(["Risk LOW"]) == "low"
    assert lab.parse_risk_level(["Risk MEDIUM"]) == "medium"
    assert lab.parse_risk_level(["Risk HIGH"]) == "high"


def test_parse_risk_level_paren():
    assert lab.parse_risk_level(["Risiko 20/100 (low) → risikobereinigt 80."]) == "low"


def test_parse_risk_level_none():
    assert lab.parse_risk_level(["nichts hier"]) == lab.UNKNOWN


def test_parse_score():
    assert lab.parse_score(["Score 73/100"]) == 73.0


def test_parse_score_ignores_market_score():
    assert lab.parse_score(["Marktqualität: Market Score 70/100."]) is None


def test_parse_score_none():
    assert lab.parse_score(["kein score"]) is None


def test_parse_score_float():
    assert lab.parse_score(["Score 61.5/100"]) == 61.5


def test_classify_outcome_win():
    assert lab.classify_outcome(10.0) == "win"


def test_classify_outcome_loss():
    assert lab.classify_outcome(-10.0) == "loss"


def test_classify_outcome_breakeven():
    assert lab.classify_outcome(0.0) == "breakeven"


def test_classify_outcome_epsilon():
    assert lab.classify_outcome(0.005, breakeven_epsilon=0.01) == "breakeven"


def test_score_band_low():
    assert lab.score_band(30.0, 40.0, 70.0) == "low"


def test_score_band_medium():
    assert lab.score_band(55.0, 40.0, 70.0) == "medium"


def test_score_band_high():
    assert lab.score_band(80.0, 40.0, 70.0) == "high"


def test_score_band_none():
    assert lab.score_band(None, 40.0, 70.0) == lab.UNKNOWN


def test_holding_band_ranges():
    assert lab.holding_band(0.5, [1, 3, 7]) == "0-1"
    assert lab.holding_band(2.0, [1, 3, 7]) == "1-3"
    assert lab.holding_band(5.0, [1, 3, 7]) == "3-7"


def test_holding_band_above():
    assert lab.holding_band(10.0, [1, 3, 7]) == ">7"


def test_holding_band_zero_unknown():
    assert lab.holding_band(0.0, [1, 3, 7]) == lab.UNKNOWN


def test_label_of_present():
    assert lab.label_of({"pattern": "fvg"}, "pattern") == "fvg"


def test_label_of_missing():
    assert lab.label_of({}, "pattern") == lab.UNKNOWN


def test_label_of_empty_value():
    assert lab.label_of({"pattern": ""}, "pattern") == lab.UNKNOWN
