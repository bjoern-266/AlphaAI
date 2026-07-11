"""Tests für das Laden der Analytics-Regeln."""

from __future__ import annotations

from pathlib import Path

import pytest

from engines.analytics_engine import (
    AnalyticsRulesError,
    load_analytics_rules,
    load_analytics_rules_from_dict,
)


def _valid(**over):
    data = {
        "meta": {"version": 5},
        "analysis": {"base_capital": 20000.0, "holding_bands": [1, 5]},
        "trade_statistics": {"enabled": True},
    }
    data.update(over)
    return data


def test_load_default_rules_from_file():
    rules = load_analytics_rules()
    assert rules.version >= 1
    assert "trade_statistics" in rules.models
    assert rules.config["base_capital"] > 0


def test_load_from_dict():
    rules = load_analytics_rules_from_dict(_valid())
    assert rules.version == 5
    assert rules.config["base_capital"] == 20000.0
    assert rules.config["holding_bands"] == [1, 5]


def test_missing_file_raises():
    with pytest.raises(AnalyticsRulesError):
        load_analytics_rules(Path("/nonexistent/analytics_rules.toml"))


def test_no_models_raises():
    with pytest.raises(AnalyticsRulesError):
        load_analytics_rules_from_dict({"meta": {"version": 1}, "analysis": {}})


def test_invalid_analysis_section_raises():
    with pytest.raises(AnalyticsRulesError):
        load_analytics_rules_from_dict(_valid(analysis=[1, 2]))


def test_zero_base_capital_raises():
    with pytest.raises(AnalyticsRulesError):
        load_analytics_rules_from_dict(_valid(analysis={"base_capital": 0.0}))


def test_negative_base_capital_raises():
    with pytest.raises(AnalyticsRulesError):
        load_analytics_rules_from_dict(_valid(analysis={"base_capital": -5.0}))


def test_defaults_applied_without_analysis():
    rules = load_analytics_rules_from_dict(
        {"meta": {"version": 1}, "trade_statistics": {"enabled": True}}
    )
    assert rules.config == {}


def test_reserved_sections_excluded():
    rules = load_analytics_rules_from_dict(_valid())
    assert "meta" not in rules.models
    assert "analysis" not in rules.models


def test_models_kept():
    rules = load_analytics_rules_from_dict(_valid(risk_analysis={"enabled": True}))
    assert "risk_analysis" in rules.models
