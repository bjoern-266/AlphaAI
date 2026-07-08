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
class CacheConfig:
    """Einstellungen für den Marktdaten-Cache.

    Attributes:
        enabled: Ob der Cache grundsätzlich verwendet wird.
        historical_ttl_seconds: Lebensdauer historischer (Tages-)Daten.
        intraday_ttl_seconds: Lebensdauer von Intraday-Daten.
        tickerlist_ttl_seconds: Lebensdauer zwischengespeicherter Tickerlisten.
    """

    enabled: bool
    historical_ttl_seconds: int
    intraday_ttl_seconds: int
    tickerlist_ttl_seconds: int


@dataclass(frozen=True, slots=True)
class DataConfig:
    """Einstellungen der Data Layer.

    Attributes:
        default_provider: Name des standardmäßig genutzten Providers.
        default_interval: Standard-Kerzenintervall (z. B. ``"1d"``).
        default_timeframe: Standard-Zeitraum/Rückschau (z. B. ``"6mo"``).
        cache: Cache-Einstellungen.
    """

    default_provider: str
    default_interval: str
    default_timeframe: str
    cache: CacheConfig


@dataclass(frozen=True, slots=True)
class ScannerConfig:
    """Einstellungen des Scanners.

    Attributes:
        max_workers: Vorbereitete maximale Anzahl paralleler Worker. Aktuell
            findet keine Parallelisierung statt; der Wert wird lediglich in die
            Anfrage übernommen.
        requested_features: Standardliste der später anzuwendenden
            Analysebausteine (z. B. ``"indicators"``, ``"patterns"``). Im
            Scanner Core werden diese nur mitgeführt, nicht ausgeführt.
    """

    max_workers: int
    requested_features: tuple[str, ...]


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
        data: Einstellungen der Data Layer.
        scanner: Einstellungen des Scanners.
        markets: Liste der zu beobachtenden Märkte/Symbole.
    """

    account: AccountConfig
    risk: RiskConfig
    trading_hours: TradingHoursConfig
    data: DataConfig
    scanner: ScannerConfig
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
    if not settings.data.default_provider:
        raise ConfigError("data.default_provider darf nicht leer sein.")
    if not settings.data.default_interval:
        raise ConfigError("data.default_interval darf nicht leer sein.")
    if not settings.data.default_timeframe:
        raise ConfigError("data.default_timeframe darf nicht leer sein.")
    for ttl_name in ("historical_ttl_seconds", "intraday_ttl_seconds", "tickerlist_ttl_seconds"):
        if getattr(settings.data.cache, ttl_name) < 0:
            raise ConfigError(f"data.cache.{ttl_name} darf nicht negativ sein.")
    if settings.scanner.max_workers < 1:
        raise ConfigError("scanner.max_workers muss mindestens 1 sein.")


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
    data_raw = _require_section(data, "data")
    cache_raw = _require_section(data_raw, "cache")
    scanner_raw = _require_section(data, "scanner")
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
        data=DataConfig(
            default_provider=str(_require(data_raw, "default_provider", "data")),
            default_interval=str(_require(data_raw, "default_interval", "data")),
            default_timeframe=str(_require(data_raw, "default_timeframe", "data")),
            cache=CacheConfig(
                enabled=bool(_require(cache_raw, "enabled", "data.cache")),
                historical_ttl_seconds=int(
                    _require(cache_raw, "historical_ttl_seconds", "data.cache")
                ),
                intraday_ttl_seconds=int(_require(cache_raw, "intraday_ttl_seconds", "data.cache")),
                tickerlist_ttl_seconds=int(
                    _require(cache_raw, "tickerlist_ttl_seconds", "data.cache")
                ),
            ),
        ),
        scanner=ScannerConfig(
            max_workers=int(_require(scanner_raw, "max_workers", "scanner")),
            requested_features=tuple(
                str(feature) for feature in _require(scanner_raw, "requested_features", "scanner")
            ),
        ),
        markets=list(_require(markets_raw, "symbols", "markets")),
    )

    _validate(settings)
    return settings
