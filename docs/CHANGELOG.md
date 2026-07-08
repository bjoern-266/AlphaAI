# Changelog

_Wird nach jedem Sprint automatisch aktualisiert._ Das Format orientiert sich
an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/) und
[Semantic Versioning](https://semver.org/lang/de/).

## [0.2.0] – 2026-07-08 – Sprint 2: Data Layer

### Hinzugefügt

- **Data Layer** zur Beschaffung, Prüfung und Zwischenspeicherung von
  Marktdaten:
  - `data/market_request.py` – unveränderliches `MarketRequest` (Symbole,
    Zeitraum, Intervall, Markt, Cache-Flag) inkl. stabilem Cache-Schlüssel.
  - `data/market_result.py` – `MarketResult` mit kanonischem OHLCV-Schema
    (inkl. Adjusted Close und Volumen), Status, Metadaten und Fehlern.
  - `data/cache.py` – `TTLCache` mit kategoriespezifischer TTL (historisch,
    intraday, Tickerlisten) und injizierbarer Uhr.
  - `data/validator.py` – Prüfung auf NaN, nicht-positive Preise,
    doppelte/unsortierte Zeitstempel, fehlende Kerzen (Warnung) und ungültige
    Symbole.
  - `data/universe.py` + `config/universe.toml` – Universen für DAX, MDAX,
    SDAX, TecDAX, S&P 500, Nasdaq-100, Russell 2000 sowie vorbereitetes
    ETF-Universum.
  - `data/market_data_engine.py` – `MarketDataEngine` als oberste
    Zugriffsschicht (kennt nur das Repository).
- **Provider-Schicht:**
  - `providers/base_provider.py` – abstrakte Provider-Schnittstelle.
  - `providers/yahoo_provider.py` – Yahoo-Finance-Provider (yfinance) mit
    injizierbarer Download-Funktion.
  - `providers/provider_factory.py` – Provider-Erzeugung nach Name;
    `finnhub`, `polygon`, `alphavantage`, `iex` sind vorbereitet, aber nicht
    implementiert.
- **Repository-Schicht:**
  - `repositories/market_repository.py` – kapselt Provider, Cache und Validator.
  - `repositories/repository_factory.py` – Verdrahtung aus der Konfiguration.
- **Konfiguration:** neuer `[data]`- und `[data.cache]`-Bereich in
  `settings.toml`; `core/config.py` um `DataConfig`/`CacheConfig` erweitert.
- **Tests:** von 14 auf 68 erhöht (Data Layer vollständig ohne Netzwerk
  testbar).

### Hinweis

Bewusst weiterhin nicht enthalten: Scanner, Indikatoren (EMA/RSI/FVG), Scores
und jegliche Handelslogik.

## [0.1.0] – 2026-07-08 – Sprint 1: Fundament

### Hinzugefügt

- Modulare Projektstruktur unter `AlphaAI/` (core, config, knowledge, data,
  providers, scanner, engines, patterns, strategies, dashboard, database,
  models, tests, docs, logs, output, scripts).
- Kernschicht `core/`:
  - `paths.py` – zentrale Projektpfade, keine hartcodierten Pfade.
  - `exceptions.py` – projektweite Fehlerklassen (`AlphaAIError`, `ConfigError`).
  - `config.py` – Laden/Validieren von `settings.toml` in typisierte,
    unveränderliche Datenklassen (Fail-Fast).
  - `logging_config.py` – einheitliches, idempotentes Logging (Konsole + Datei).
- Konfigurationsdatei `config/settings.toml` (Depot, Broker, Fractional
  Shares, Risiko, Handelszeiten, Märkte).
- Wissensbasis `knowledge/` (Markdown-Regeln + TOML-Parameterdateien).
- Prüfskript `scripts/check_setup.py`.
- Dokumentation `docs/` (Architektur, Status, Roadmap, Changelog, Handover,
  AI-Kontext, Entscheidungen).
- Basistests (`tests/`) für Konfiguration, Logging und Projektstruktur.
- Werkzeugkonfiguration in `pyproject.toml` (Black, Ruff, pytest).
- `.gitignore` für Python- und Laufzeit-Artefakte.

### Hinweis

Bewusst noch nicht enthalten: Scanner, Datenquellen, Indikatoren, Muster,
Strategien und Handelslogik. Diese folgen ab Sprint 2.
