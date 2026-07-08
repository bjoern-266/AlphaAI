"""Laden und Validieren der Projektkonfiguration.

Die Konfiguration wird aus ``config/settings.toml`` gelesen und in typisierte,
unveränderliche Datenklassen überführt. Dadurch ist im restlichen Code
sofort ersichtlich, welche Felder existieren, und fehlerhafte Werte werden
früh und mit klarer Meldung erkannt (Fail-Fast).

Bewusste Entscheidung: Es wird ausschließlich die Standardbibliothek
(``tomllib``, ``dataclasses``) verwendet. Das hält das Fundament
abhängigkeitsarm und leicht verständlich. Details siehe ``docs/DECISIONS.md``.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.exceptions import ConfigError
from core.paths import SETTINGS_FILE


@dataclass(frozen=True, slots=True)
class AccountConfig:
    """Depot- und Broker-Angaben.

    Attributes:
        capital: Depotgröße in der Kontowährung.
        currency: Kontowährung als ISO-Code (z. B. ``"EUR"``).
        broker: Name des Brokers (freier Text, dient der Dokumentation).
        fractional_shares: Ob der Broker Bruchstücke von Aktien erlaubt.
    """

    capital: float
    currency: str
    broker: str
    fractional_shares: bool


@dataclass(frozen=True, slots=True)
class RiskConfig:
    """Risikoparameter für die Positionsberechnung.

    Attributes:
        risk_per_trade_pct: Anteil des Depots, der pro Trade riskiert wird
            (0.01 = 1 %).
        max_open_positions: Maximale Anzahl gleichzeitig offener Positionen.
        max_daily_loss_pct: Maximaler Tagesverlust als Depotanteil, ab dem
            keine neuen Empfehlungen mehr erzeugt werden sollen.
    """

    risk_per_trade_pct: float
    max_open_positions: int
    max_daily_loss_pct: float


@dataclass(frozen=True, slots=True)
class TradingHoursConfig:
    """Handelszeiten für die Analyse.

    Attributes:
        timezone: Zeitzone der Handelszeiten (IANA-Name, z. B.
            ``"Europe/Berlin"``).
        session_start: Sitzungsbeginn im Format ``"HH:MM"``.
        session_end: Sitzungsende im Format ``"HH:MM"``.
    """

    timezone: str
    session_start: str
    session_end: str


@dataclass(frozen=True, slots=True)
class Settings:
    """Vollständige, validierte Projektkonfiguration.

    Diese Klasse bündelt alle Teilkonfigurationen und wird über
    :func:`load_settings` erzeugt. Sie ist unveränderlich und kann daher
    gefahrlos per Dependency Injection weitergereicht werden.

    Attributes:
        account: Depot- und Broker-Angaben.
        risk: Risikoparameter.
        trading_hours: Handelszeiten.
        markets: Liste der zu beobachtenden Märkte/Symbole.
    """

    account: AccountConfig
    risk: RiskConfig
    trading_hours: TradingHoursConfig
    markets: list[str] = field(default_factory=list)


def _require_section(data: dict[str, Any], name: str) -> dict[str, Any]:
    """Gibt eine Pflicht-Sektion zurück oder wirft :class:`ConfigError`."""
    section = data.get(name)
    if not isinstance(section, dict):
        raise ConfigError(f"Fehlende oder ungültige Sektion '[{name}]' in der Konfiguration.")
    return section


def _require(section: dict[str, Any], key: str, section_name: str) -> Any:
    """Gibt einen Pflichtwert zurück oder wirft :class:`ConfigError`."""
    if key not in section:
        raise ConfigError(f"Fehlender Schlüssel '{key}' in Sektion '[{section_name}]'.")
    return section[key]


def _validate(settings: Settings) -> None:
    """Prüft die geladenen Werte auf fachliche Plausibilität.

    Raises:
        ConfigError: Wenn ein Wert außerhalb des zulässigen Bereichs liegt.
    """
    if settings.account.capital <= 0:
        raise ConfigError("account.capital muss größer als 0 sein.")
    if not 0 < settings.risk.risk_per_trade_pct < 1:
        raise ConfigError("risk.risk_per_trade_pct muss zwischen 0 und 1 liegen (z. B. 0.01).")
    if not 0 < settings.risk.max_daily_loss_pct < 1:
        raise ConfigError("risk.max_daily_loss_pct muss zwischen 0 und 1 liegen.")
    if settings.risk.max_open_positions < 1:
        raise ConfigError("risk.max_open_positions muss mindestens 1 sein.")
    if not settings.markets:
        raise ConfigError("Es muss mindestens ein Markt in [markets].symbols konfiguriert sein.")


def load_settings(path: Path | None = None) -> Settings:
    """Lädt und validiert die Projektkonfiguration.

    Args:
        path: Optionaler Pfad zur TOML-Datei. Standardmäßig wird
            ``config/settings.toml`` verwendet.

    Returns:
        Die vollständig validierte :class:`Settings`-Instanz.

    Raises:
        ConfigError: Wenn die Datei fehlt oder ungültige/fehlende Werte enthält.
    """
    settings_path = path or SETTINGS_FILE
    if not settings_path.is_file():
        raise ConfigError(f"Konfigurationsdatei nicht gefunden: {settings_path}")

    try:
        with settings_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"Konfiguration ist kein gültiges TOML: {error}") from error

    account_raw = _require_section(data, "account")
    risk_raw = _require_section(data, "risk")
    hours_raw = _require_section(data, "trading_hours")
    markets_raw = _require_section(data, "markets")

    settings = Settings(
        account=AccountConfig(
            capital=float(_require(account_raw, "capital", "account")),
            currency=str(_require(account_raw, "currency", "account")),
            broker=str(_require(account_raw, "broker", "account")),
            fractional_shares=bool(_require(account_raw, "fractional_shares", "account")),
        ),
        risk=RiskConfig(
            risk_per_trade_pct=float(_require(risk_raw, "risk_per_trade_pct", "risk")),
            max_open_positions=int(_require(risk_raw, "max_open_positions", "risk")),
            max_daily_loss_pct=float(_require(risk_raw, "max_daily_loss_pct", "risk")),
        ),
        trading_hours=TradingHoursConfig(
            timezone=str(_require(hours_raw, "timezone", "trading_hours")),
            session_start=str(_require(hours_raw, "session_start", "trading_hours")),
            session_end=str(_require(hours_raw, "session_end", "trading_hours")),
        ),
        markets=list(_require(markets_raw, "symbols", "markets")),
    )

    _validate(settings)
    return settings
