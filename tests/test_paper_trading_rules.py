"""Tests für das Laden der Paper-Trading-Regeln."""

from __future__ import annotations

from pathlib import Path

import pytest

from engines.paper_trading_engine import (
    PaperTradingRulesError,
    load_paper_trading_rules,
    load_paper_trading_rules_from_dict,
)


def _valid(**over):
    data = {
        "meta": {"version": 4},
        "runner": {"warmup_bars": 50, "step": 2, "max_holding_days": 7, "trailing_distance": 0.0},
        "statistics_model": {"enabled": True},
    }
    data.update(over)
    return data


def test_load_default_rules_from_file():
    rules = load_paper_trading_rules()
    assert rules.version >= 1
    assert "statistics_model" in rules.models
    assert rules.runner.warmup_bars >= 1


def test_load_from_dict():
    rules = load_paper_trading_rules_from_dict(_valid())
    assert rules.version == 4
    assert rules.runner.warmup_bars == 50
    assert rules.runner.step == 2
    assert rules.runner.max_holding_days == 7


def test_missing_file_raises():
    with pytest.raises(PaperTradingRulesError):
        load_paper_trading_rules(Path("/nonexistent/paper_trading_rules.toml"))


def test_no_models_raises():
    with pytest.raises(PaperTradingRulesError):
        load_paper_trading_rules_from_dict({"meta": {"version": 1}, "runner": {}})


def test_invalid_runner_section_raises():
    with pytest.raises(PaperTradingRulesError):
        load_paper_trading_rules_from_dict(_valid(runner=[1, 2]))


def test_zero_warmup_raises():
    with pytest.raises(PaperTradingRulesError):
        load_paper_trading_rules_from_dict(_valid(runner={"warmup_bars": 0}))


def test_zero_max_holding_raises():
    with pytest.raises(PaperTradingRulesError):
        load_paper_trading_rules_from_dict(_valid(runner={"max_holding_days": 0}))


def test_negative_trailing_raises():
    with pytest.raises(PaperTradingRulesError):
        load_paper_trading_rules_from_dict(
            _valid(runner={"warmup_bars": 5, "max_holding_days": 5, "trailing_distance": -1.0})
        )


def test_defaults_applied_without_runner():
    rules = load_paper_trading_rules_from_dict(
        {"meta": {"version": 1}, "statistics_model": {"enabled": True}}
    )
    assert rules.runner.warmup_bars == 200
    assert rules.runner.max_holding_days == 10


def test_reserved_sections_excluded():
    rules = load_paper_trading_rules_from_dict(_valid())
    assert "meta" not in rules.models
    assert "runner" not in rules.models
