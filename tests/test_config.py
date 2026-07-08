"""Tests für das Laden und Validieren der Konfiguration."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.config import Settings, load_settings
from core.exceptions import ConfigError
from core.paths import SETTINGS_FILE

VALID_TOML = """
[account]
capital = 10000.0
currency = "EUR"
broker = "Test Broker"
fractional_shares = true

[risk]
risk_per_trade_pct = 0.01
max_open_positions = 5
max_daily_loss_pct = 0.03

[trading_hours]
timezone = "Europe/Berlin"
session_start = "09:00"
session_end = "17:30"

[data]
default_provider = "yahoo"
default_interval = "1d"
default_timeframe = "6mo"

[data.cache]
enabled = true
historical_ttl_seconds = 86400
intraday_ttl_seconds = 300
tickerlist_ttl_seconds = 604800

[markets]
symbols = ["AAPL", "MSFT"]
"""


def _write(tmp_path: Path, content: str) -> Path:
    """Schreibt TOML-Inhalt in eine temporäre Datei und gibt den Pfad zurück."""
    target = tmp_path / "settings.toml"
    target.write_text(content, encoding="utf-8")
    return target


def test_load_valid_settings(tmp_path: Path) -> None:
    settings = load_settings(_write(tmp_path, VALID_TOML))

    assert isinstance(settings, Settings)
    assert settings.account.capital == 10000.0
    assert settings.account.currency == "EUR"
    assert settings.account.fractional_shares is True
    assert settings.risk.max_open_positions == 5
    assert settings.trading_hours.timezone == "Europe/Berlin"
    assert settings.markets == ["AAPL", "MSFT"]
    assert settings.data.default_provider == "yahoo"
    assert settings.data.default_interval == "1d"
    assert settings.data.cache.enabled is True
    assert settings.data.cache.historical_ttl_seconds == 86400


def test_settings_are_immutable(tmp_path: Path) -> None:
    settings = load_settings(_write(tmp_path, VALID_TOML))
    with pytest.raises(AttributeError):
        settings.account.capital = 1.0  # type: ignore[misc]


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="nicht gefunden"):
        load_settings(tmp_path / "does_not_exist.toml")


def test_missing_section_raises(tmp_path: Path) -> None:
    content = VALID_TOML.replace("[risk]", "[risk_disabled]")
    with pytest.raises(ConfigError, match=r"\[risk\]"):
        load_settings(_write(tmp_path, content))


def test_invalid_risk_value_raises(tmp_path: Path) -> None:
    content = VALID_TOML.replace("risk_per_trade_pct = 0.01", "risk_per_trade_pct = 1.5")
    with pytest.raises(ConfigError, match="risk_per_trade_pct"):
        load_settings(_write(tmp_path, content))


def test_empty_markets_raises(tmp_path: Path) -> None:
    content = VALID_TOML.replace('symbols = ["AAPL", "MSFT"]', "symbols = []")
    with pytest.raises(ConfigError, match="Markt"):
        load_settings(_write(tmp_path, content))


def test_missing_data_section_raises(tmp_path: Path) -> None:
    content = VALID_TOML.replace("[data]", "[data_disabled]")
    with pytest.raises(ConfigError, match=r"\[data\]"):
        load_settings(_write(tmp_path, content))


def test_negative_cache_ttl_raises(tmp_path: Path) -> None:
    content = VALID_TOML.replace("historical_ttl_seconds = 86400", "historical_ttl_seconds = -1")
    with pytest.raises(ConfigError, match="historical_ttl_seconds"):
        load_settings(_write(tmp_path, content))


def test_shipped_settings_file_is_valid() -> None:
    """Die mitgelieferte config/settings.toml muss ladbar und gültig sein."""
    settings = load_settings(SETTINGS_FILE)
    assert settings.account.capital > 0
    assert settings.markets
