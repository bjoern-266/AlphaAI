# Changelog

_Wird nach jedem Sprint automatisch aktualisiert._ Das Format orientiert sich
an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/) und
[Semantic Versioning](https://semver.org/lang/de/).

## [0.4.0] – 2026-07-08 – Sprint 4: Indicator Engine

### Hinzugefügt

- **Indicator Engine** (berechnet Kennzahlen, keine Entscheidungen/Scores/Signale):
  - `engines/indicator_engine.py` – `IndicatorEngine` (Orchestrierung,
    Validierung, optionaler Cache) + `load_indicator_rules`.
  - `engines/indicator_registry.py` – `IndicatorRegistry` (einzige
    Erweiterungsstelle) + `build_default_registry`.
  - `engines/indicator_result.py` – `IndicatorResult` mit typisierten Zugriffen
    (EMA20/50/200, RSI14, ATR14, VWAP, MACD/Signal/Histogramm, RelativeVolume,
    ADX, BollingerBands, Stochastic, OBV, VolumeProfile) plus
    `calculation_time`, `valid`, `warnings`, `metadata`.
  - `engines/indicator_cache.py` – `IndicatorCache` (FIFO, Treffer-/Fehltreffer).
- **11 unabhängige Indikatoren** in `indicators/` (je eigene Datei): `ema`,
  `rsi`, `atr`, `vwap`, `macd`, `relative_volume`, `adx`, `bollinger`,
  `stochastic`, `obv`, `volume_profile`; gemeinsame Schnittstelle/Hilfen in
  `indicators/base.py`.
- **Konfiguration:** `knowledge/indicator_rules.toml` mit Parametern aller
  Indikatoren (keine Hardcodes im Code).
- **Validierung:** genug Kerzen, NaN, Division durch Null (via `safe_divide`),
  fehlende Volumendaten, zu wenig Historie.
- **Multi-Timeframe:** Architektur vorbereitet (Timeframe-Label), nicht
  implementiert.
- **Tests:** von 95 auf 148 erhöht (je Indikator, Registry, Cache, Engine,
  Validierung, Performance). Testabdeckung neuer Module 92 %.

### Qualitätsprüfung

Import-Zyklen: 0. Indikator-Unabhängigkeit: 0 Verstöße. SOLID-Heuristik:
0 Verstöße. Details in `HANDOVER.md`.

### Hinweis

Bewusst nicht enthalten: FVG, BOS, CHoCH, Order Blocks, Score-/Risk-/
Recommendation-Engine und Dashboard-Logik.

## [0.3.0] – 2026-07-08 – Sprint 3: Scanner Core

### Hinzugefügt

- **Scanner Core** (reine Orchestrierung, keine Analyse):
  - `scanner/scan_request.py` – `ScanRequest` (Markt, Universum, Symbole,
    Provider, Timeframe, Interval, UseCache, RequestedFeatures, MaxWorkers) und
    `build_scan_request` (Standards aus Konfiguration).
  - `scanner/scan_result.py` – `ScanResult` je Symbol mit vorbereiteten, leeren
    Analysefeldern (Indicators, Patterns, Score, Risk, Recommendation) sowie
    `ScanReport`-Container.
  - `scanner/scan_statistics.py` – `ScanStatistics` (Start/Ende, Laufzeit,
    Symbolzahl, Provider, Cache-Treffer/-Fehltreffer, Fehler).
  - `scanner/scan_pipeline.py` – `ScanPipeline` (Universum laden →
    MarketDataEngine aufrufen → Daten sammeln → ScanResult erzeugen).
  - `scanner/scanner_engine.py` – `ScannerEngine` (kennt nur die Pipeline;
    Scan-Logging).
  - `scanner/scanner_manager.py` – `ScannerManager` (Mehrfach-Scans, sequenziell;
    Parallelisierung über `max_workers` vorbereitet).
- **Konfiguration:** neuer `[scanner]`-Bereich (`max_workers`,
  `requested_features`); `core/config.py` um `ScannerConfig` erweitert.
- **Data Layer:** `MarketResult.metadata["cache_hit"]` gesetzt vom Repository
  (Basis der Cache-Statistik).
- **Tests:** von 68 auf 95 erhöht (Request, Result, Statistik, Pipeline, Engine,
  Manager).

### Hinweis

Bewusst weiterhin nicht enthalten: Indikatoren (EMA/RSI/ATR/VWAP/MACD), Muster
(FVG/BOS/CHoCH), Scores, Buy/Sell-Signale und Dashboard-Ansicht.

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
