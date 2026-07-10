"""Tests für das Laden der Backtest-Regeln."""

from __future__ import annotations

import pytest

from engines.backtest_engine import (
    BacktestRulesError,
    load_backtest_rules,
    load_backtest_rules_from_dict,
)


def _valid_dict(**over):
    data = {
        "meta": {"version": 3},
        "engine": {"warmup_bars": 50, "step": 2, "min_history_bars": 60},
        "simulation": {"max_holding_bars": 5, "apply_costs": True, "breakeven_epsilon": 0.0},
        "performance_model": {"enabled": True},
    }
    data.update(over)
    return data


def test_load_default_rules_from_file():
    rules = load_backtest_rules()
    assert rules.version >= 1
    assert "performance_model" in rules.models
    assert rules.runner.warmup_bars >= 1
    assert rules.simulation.max_holding_bars >= 1


def test_load_from_dict_parses_sections():
    rules = load_backtest_rules_from_dict(_valid_dict())
    assert rules.version == 3
    assert rules.runner.warmup_bars == 50
    assert rules.runner.step == 2
    assert rules.simulation.max_holding_bars == 5


def test_missing_file_raises():
    from pathlib import Path

    with pytest.raises(BacktestRulesError):
        load_backtest_rules(Path("/nonexistent/backtest_rules.toml"))


def test_no_models_raises():
    data = {"meta": {"version": 1}, "engine": {}, "simulation": {}}
    with pytest.raises(BacktestRulesError):
        load_backtest_rules_from_dict(data)


def test_invalid_engine_section_raises():
    with pytest.raises(BacktestRulesError):
        load_backtest_rules_from_dict(_valid_dict(engine=[1, 2, 3]))


def test_zero_warmup_raises():
    with pytest.raises(BacktestRulesError):
        load_backtest_rules_from_dict(_valid_dict(engine={"warmup_bars": 0}))


def test_zero_max_holding_raises():
    with pytest.raises(BacktestRulesError):
        load_backtest_rules_from_dict(_valid_dict(simulation={"max_holding_bars": 0}))


def test_negative_breakeven_raises():
    with pytest.raises(BacktestRulesError):
        load_backtest_rules_from_dict(
            _valid_dict(simulation={"max_holding_bars": 5, "breakeven_epsilon": -1.0})
        )


def test_defaults_applied_when_sections_absent():
    data = {"meta": {"version": 1}, "performance_model": {"enabled": True}}
    rules = load_backtest_rules_from_dict(data)
    assert rules.runner.warmup_bars == 200
    assert rules.simulation.max_holding_bars == 20


def test_models_exclude_reserved_sections():
    rules = load_backtest_rules_from_dict(_valid_dict())
    assert "meta" not in rules.models
    assert "engine" not in rules.models
    assert "simulation" not in rules.models
