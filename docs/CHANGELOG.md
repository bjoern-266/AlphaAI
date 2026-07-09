# Changelog

_Wird nach jedem Sprint automatisch aktualisiert._ Das Format orientiert sich
an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/) und
[Semantic Versioning](https://semver.org/lang/de/).

## [0.9.5] – 2026-07-09 – Sprint 9.5: End-to-End Integration & Validation

Reine Integration, Validierung und Qualitätssicherung der bestehenden
Architektur. **Keine** neuen Features, **keine** neue Engine, **keine**
Engine-Änderung, **keine** Order-/Broker-/Dashboard-Bausteine.

### Hinzugefügt

- **IntegrationRunner** (`pipeline/runner.py`): verbindet die komplette Kette
  `MarketData → IndicatorEngine → PatternEngine → StrategyEngine → ScoreEngine
  → RiskEngine → RecommendationEngine` End-to-End. Jede Engine erhält nur
  vorgelagerte Ausgaben; keine Schicht wird umgangen. `from_config()`, `run`,
  `run_all`, `run_frame`.
- **PipelineResult** (`models/pipeline.py`, `frozen`): bündelt die Ausgaben
  aller Stufen für ein Symbol.
- **Konsistenzprüfungen** (`pipeline/consistency.py`): `verify_pipeline` stellt
  sicher, dass jede Empfehlung genau einen RiskResult, jeder RiskResult genau
  einen ScoreResult und jeder ScoreResult genau einen StrategyResult besitzt,
  alle IDs eindeutig und alle Referenzen gültig sind.
- **13 echte Marktszenarien** (`tests/scenarios.py`, deterministisch, kein Mock):
  Trend auf/ab, Seitwärts, hohe/niedrige Volatilität, bullischer/bärischer
  Ausbruch, niedrige/hohe Liquidität, Gaps, Choppy, schwache Datenqualität, zu
  kurze/fehlende Historie.
- **180 Integrations-Tests** (`tests/test_integration_pipeline.py`): echte
  End-to-End-Durchläufe; prüfen Konsistenz, Stufen-/Handlungs-Validität,
  Wertebereiche, Erklärbarkeit und die zentralen Invarianten (hohes Risiko
  deckelt, Score allein nie BUY, No-Trade als normales Ergebnis).
- **Reports:** `docs/PIPELINE.md` (vollständiger Datenfluss) und
  `docs/VALIDATION_REPORT.md` (Szenarien, Ergebnisse, Statistiken, Auffälligkeiten,
  Verbesserungsvorschläge).
- Neues Paket `pipeline` in `pyproject.toml` und im Qualitäts-Check registriert.

### Validierung (Kurzfassung)

Über 180 Tests: **0** Konsistenzverstöße; alle Entscheidungs-Invarianten
bestätigt. Als **Auffälligkeiten** dokumentiert (ohne Engine-Änderung): auf
idealisierten Trends ist STRONG_BUY häufig; die Stufe misst Konviktion, nicht
Richtung (ein bärisches Setup erhält „STRONG_BUY"); WAIT/AVOID traten nicht auf;
Risiko blieb LOW. Priorisierte Verbesserungsvorschläge in
`docs/VALIDATION_REPORT.md`.

### Qualitätsprüfung

Import-Zyklen: 0. Entities-Schicht `models/`: 0. Plugin-Unabhängigkeit/SOLID: 0.
Immutability vollständig. `ruff`/`black` konform. 682 Tests grün (+180).

### ADR

ADR-029 (End-to-End-Integration: IntegrationRunner, Konsistenzprüfungen,
Validierungsstrategie).

## [0.9.0] – 2026-07-09 – Sprint 9: Recommendation Engine

Letzte fachliche Entscheidungsschicht auf dem konsolidierten Fundament. Die
Recommendation Engine kombiniert `StrategyReport`, `ScoreReport` und
`RiskReport` zu einer objektiven, **vollständig erklärbaren** Empfehlung. Sie
eröffnet **keine** Position, sendet **keine** Order und kommuniziert **nicht**
mit Brokern. `WAIT`/`AVOID` sind vollwertige Empfehlungen.

### Hinzugefügt

- **Recommendation Engine** (`Strategy+Score+Risk → RecommendationEngine → RecommendationReport`):
  - `engines/recommendation_engine.py` – `RecommendationEngine` (Matching der
    drei Reports je Hypothese, Validierung, optionaler Cache,
    `dataclasses.replace()` für die Rechenzeit) + `load_recommendation_rules`.
  - `engines/recommendation_registry.py` – `RecommendationRegistry` (einzige
    Erweiterungsstelle) + `build_default_registry`.
  - `engines/recommendation_cache.py` – `RecommendationCache` (FIFO, generisch).
  - `engines/recommendation_result.py` – Re-Export aus `models.recommendation`.
- **Domänenmodelle** in `models/recommendation.py` (alle `frozen`):
  `RecommendationLevel` (STRONG_BUY/BUY/WATCH/WAIT/AVOID), `SuggestedAction`
  (OPEN/WAIT/MONITOR/SKIP), `RecommendationFactor`, `RecommendationModelOutput`,
  `RecommendationContext`, `RecommendationResult`, `RecommendationReport`.
- **5 unabhängige Modelle** in `recommendation/` (je eigene Datei):
  `decision_model`, `recommendation_model`, `confidence_model`, `summary_model`,
  `explanation_model`. Gemeinsame Faktor-/Rating-/Confidence-Berechnung und die
  No-Trade-Gates in `recommendation/base.py`; kein Modell hängt von einem anderen ab.
- **Entscheidungslogik über 6 Faktoren** (Strategie, Score, Risiko, Konsens,
  Marktqualität, Datenqualität): Das Gesamtrating ist ihre gewichtete Summe.
  Der Score-Anteil ist bewusst begrenzt (0,25) und der Konsens belohnt **Breite**
  (mehrere unabhängige, gleichgerichtete Strategien) – ein hoher Score allein
  führt daher **nie** zu BUY/STRONG_BUY. **No-Trade-Gates** deckeln zusätzlich
  bei erhöhtem Risiko, geringem Konsens, schwacher Datenqualität oder neutraler
  Richtung.
- **RecommendationResult**: Recommendation/Risk/Score/Hypothesis ID, Level,
  Confidence (0-1), Overall Rating (0-100), Suggested Action, Reasons, Warnings,
  Summary, Metadata, Timestamp – jede Empfehlung ist ohne Blackbox erklärbar.
- **Konfiguration:** `knowledge/recommendation_rules.toml` (Faktorgewichte,
  Confidence-Gewichte, Schwellen, Gates) – keine Hardcodes. `core/paths.py`:
  `RECOMMENDATION_RULES_FILE`.
- **Validierung:** fehlender/ungültiger Strategy-/Score-/Risk-Report, fehlende
  Zuordnung je Hypothese, ungültige Level/Confidence/Ratings.
- **Tests:** von 413 auf 502 erhöht (89 neue: Engine, Registry, Cache, alle
  Modelle, Validierung, Entscheidungslogik, Erklärbarkeit, No-Trade).

### Qualitätsprüfung

Import-Zyklen: 0. Recommendation-Modell-Unabhängigkeit: 0 Verstöße.
Entities-Schicht `models/`: 0 Verstöße. SOLID-Heuristik (Recommendation): 0
Verstöße. Alle Modelle unveränderlich (`frozen`). `ruff`/`black` konform. 502
Tests grün.

### ADR

ADR-028 (Recommendation Engine – Faktoren, No-Trade-Gates, Erklärbarkeit).

## [0.8.0] – 2026-07-09 – Sprint 8: Professional Risk Engine

Neue Fachschicht **Risk Engine** auf dem konsolidierten Fundament (Sprint 7.5):
frozen-Modelle in `models/`, generische `Cache`/`Registry`, Registry als einzige
Erweiterungsstelle, alle Parameter aus Config. Die Risk Engine **bewertet nur**
Risiko und empfiehlt eine Positionsgröße – **keine** Kauf-/Verkaufsentscheidung,
**keine** Position, **keine** Order, **keine** Broker-API.

### Hinzugefügt

- **Risk Engine** (`ScoreReport → RiskEngine → RiskReport`):
  - `engines/risk_engine.py` – `RiskEngine` (Orchestrierung, Validierung,
    optionaler Cache, `dataclasses.replace()` für die Rechenzeit) + `load_risk_rules`.
  - `engines/risk_registry.py` – `RiskRegistry` (einzige Erweiterungsstelle) +
    `build_default_registry`.
  - `engines/risk_cache.py` – `RiskCache` (FIFO, generisch).
  - `engines/risk_result.py` – Re-Export der Risk-Datentypen aus `models.risk`.
- **Domänenmodelle** in `models/risk.py` (alle `frozen`): `RiskLevel`,
  `OpenPosition`, `RiskComponent`, `RiskModelOutput`, `PositionSizing`,
  `RiskContext`, `RiskResult`, `RiskReport`.
- **8 unabhängige Risk-Modelle** in `risk/` (je eigene Datei): `position_sizing`,
  `volatility_risk`, `liquidity_risk`, `gap_risk`, `market_risk`,
  `correlation_risk`, `portfolio_risk`, `execution_risk`. Gemeinsame
  Schnittstelle, Positionsgrößen-Berechnung und Basiskomponenten (ATR,
  Datenqualität, News) in `risk/base.py`; kein Modell hängt von einem anderen ab.
- **10 Risikokomponenten** (getrennt gespeichert, vollständig erklärbar):
  Volatilität, Liquidität, Gap, Spread, ATR, Markt, Korrelation,
  Portfolio-Exposure, Datenqualität, News (News **vorbereitet**, neutral).
- **RiskResult**: Risk/Score/Hypothesis ID, Overall Risk (0-100), Risk Level
  (LOW/MEDIUM/HIGH), Suggested Position Size, Maximum Risk %, Maximum Portfolio
  Exposure, Estimated Shares/Order Value/Slippage/Commission, Suggested Stop
  Distance/Take Profit/Risk Reward, Risk Components, Reasons, Warnings, Metadata,
  Timestamp.
- **Positionsgröße** aus Depotgröße, Fractional Shares, Risiko je Trade, max.
  Positionen (alles aus `settings.toml`) + ATR-Stop, CRV, Slippage/Kommission
  (aus `risk_rules.toml`). **Portfolio-Risiko vorbereitet**: die Engine reicht
  bereits offene Positionen (`open_positions`) an die Modelle durch.
- **Konfiguration:** `knowledge/risk_rules.toml` (Gewichte, Schwellen,
  Modellparameter) – keine Hardcodes. `core/paths.py`: `RISK_RULES_FILE`.
- **Validierung:** fehlende Scores, negative Depotgröße, ungültige ATR/Preise,
  ungültige Positionsgrößen, ungültige Risk-Reward-Werte.
- **Tests:** von 337 auf 413 erhöht (76 neue: jedes Modell, Engine, Registry,
  Cache, Positionsgröße, Portfolio, Validierung, Immutability).

### Qualitätsprüfung

Import-Zyklen: 0. Risk-Modell-Unabhängigkeit: 0 Verstöße. Entities-Schicht
`models/`: 0 Verstöße. SOLID-Heuristik (Risk): 0 Verstöße. Alle Risk-Modelle
unveränderlich (`frozen`). `ruff`/`black` konform. 413 Tests grün.

### ADR

ADR-027 (Risk Engine – Architektur, Komponenten, Positionsgröße, Portfolio-Vorbereitung).

## [0.1.0-foundation] · [0.7.5] – 2026-07-09 – Sprint 7.5: Architecture Consolidation

Reiner, **verhaltenserhaltender** Umbau (kein neues Feature, kein geändertes
Fachverhalten). Alle bisherigen Tests bleiben unverändert grün; die öffentlichen
Importpfade bleiben über Re-Exports erhalten. Erster stabiler Fundament-Stand,
markiert mit dem Tag `v0.1.0-foundation`.

### Geändert (Konsolidierung)

- **Domänenmodelle konsolidiert** in der Entities-Schicht `models/`
  (importiert nichts aus höheren Schichten):
  - `models/market.py` (`MarketResult`, `MarketStatus`, OHLCV-Schema),
    `models/indicator.py` (`IndicatorOutput`, `IndicatorResult`),
    `models/pattern.py` (`PatternType`, `PatternDirection`, `PatternResult`,
    `PatternDetection`, `StructureBreak`, `PatternReport`),
    `models/strategy.py` (`StrategyDirection`, `StrategyContext`,
    `StrategyResult`, `StrategyEvaluation`, `StrategyReport`),
    `models/score.py` (`COMPONENT_NAMES`, `ComponentScore`, `ScoreModelOutput`,
    `ScoreContext`, `ScoreResult`, `ScoreReport`).
  - `models/risk.py` und `models/recommendation.py` als **vorbereitete**
    Platzhalter (keine Risk-/Recommendation-Engine in dieser Version).
  - Alte Pfade (`data.market_result`, `engines.*_result`, `*/base.py`) bleiben
    als **Re-Exports** vollständig gültig; die Engines und `*/base.py` enthalten
    nur noch Logik/Schnittstellen.
- **Unveränderliche Ergebnisobjekte:** alle Modelle sind `frozen`. Die Engines
  konstruieren ihr Ergebnis **einmalig am Ende** aus lokalen Akkumulatoren; die
  Rechenzeit wird über `dataclasses.replace()` gesetzt statt durch Mutation.
  Keine Engine verändert ein Ergebnisobjekt nach seiner Erstellung.
- **Generische Basis in `core/`:** `core/cache.py` (`Cache[T]`, FIFO) und
  `core/registry.py` (`Registry[T]`). Die vier Engine-Caches und -Registries
  sind nur noch dünne Spezialisierungen; öffentliches Verhalten unverändert.
- **Einheitliche Exception-Hierarchie** unter `AlphaAIError` in
  `core/exceptions.py` (`ParameterError`/`RegistryError`/`CacheError` u. a.).
  Kein blankes `ValueError`/`KeyError` mehr für fachliche Fehler; zur
  Rückwärtskompatibilität erben ausgewählte Klassen zusätzlich von
  `ValueError`/`KeyError`.
- **Kopplung reduziert:** `strategies/base.py` und `scores/base.py` importieren
  nichts mehr aus `engines` (frühere `TYPE_CHECKING`-Kopplung aufgelöst, TD-05).

### Hinzugefügt

- `scripts/quality_check.py` – versioniertes Architektur-Prüfskript
  (Import-Zyklen, Plugin-Unabhängigkeit, SOLID, saubere Entities-Schicht),
  fest verankert über `tests/test_quality.py`.
- `tests/test_immutability.py` (alle Modelle frozen) und
  `tests/test_core_generics.py` (generische Cache/Registry + Exception-Hierarchie).
- **Tests:** von 307 auf 335 erhöht (nur neue Tests; bestehende unverändert).

### Qualitätsprüfung

Import-Zyklen: 0. Entities-Schicht `models/`: 0 Verstöße. Plugin-Unabhängigkeit
(Indikatoren/Muster/Strategien/Scores): 0 Verstöße. SOLID-Heuristik: 0 Verstöße.
`ruff` und `black`: ohne Beanstandung. 335 Tests grün.

### ADRs

ADR-022 (Modelle in `models/`), ADR-023 (unveränderliche Ergebnisobjekte),
ADR-024 (generische `Cache`/`Registry`), ADR-025 (Exception-Hierarchie),
ADR-026 (PEP-695-Generics bewusst vermieden).

## [0.7.0] – 2026-07-08 – Sprint 7: Score Engine

### Hinzugefügt

- **Score Engine** (bewertet jede Hypothese objektiv; keine Entscheidung, keine
  Positionsgröße, kein Risiko):
  - `engines/score_engine.py` – `ScoreEngine` (Bewertung, Validierung,
    optionaler Cache) + `load_score_rules`.
  - `engines/score_registry.py` – `ScoreRegistry` (einzige Erweiterungsstelle)
    + `build_default_registry`.
  - `engines/score_result.py` – `ScoreResult` (Score ID, Strategy Name,
    Hypothesis ID, Total/Confidence/Quality/Consensus/Market Score, Component
    Scores, Reasons, Warnings, Metadata, Timestamp) + `ScoreReport`.
  - `engines/score_cache.py` – `ScoreCache` (FIFO).
- **5 unabhängige Score-Modelle** in `scores/` (je eigene Datei):
  `weighted_score`, `confidence_score`, `quality_score`, `consensus_score`,
  `market_score`. Gemeinsame Schnittstelle, Typen, **acht Komponenten** und die
  Gewichtsvalidierung in `scores/base.py`; kein Modell hängt von einem anderen
  ab.
- **Komponenten** (separat gespeichert): Trend, Momentum, Pattern Strength,
  Pattern Confidence, Indicator Quality, Market Context, Volume Quality,
  Data Quality.
- **Transparenz:** jeder Score über seine Komponenten erklärbar (z. B.
  `trend: 18/20`).
- **Konfiguration:** `knowledge/score_rules.toml` mit den Gewichten aller
  Modelle (Sektionsname = Modellname).
- **Validierung:** fehlende Hypothesen, ungültige Gewichte, Gewichte ≠ 100 %,
  fehlende Komponenten.
- **Tests:** von 247 auf 307 erhöht (je Modell, Registry, Cache, Engine,
  Validierung). Testabdeckung der Score-Module 96 %.

### Qualitätsprüfung

Import-Zyklen: 0. Score-Modell-Unabhängigkeit: 0 Verstöße. SOLID-Heuristik:
0 Verstöße. Details in `HANDOVER.md`.

### Hinweis

Bewusst nicht enthalten: Risk- und Recommendation-Engine sowie Dashboard-Logik.
Die Score Engine liefert ausschließlich ScoreResult.

## [0.6.0] – 2026-07-08 – Sprint 6: Strategy Engine

### Hinzugefügt

- **Strategy Engine** (kombiniert Indikatoren und Muster zu Hypothesen; keine
  Entscheidungen, kein Gesamtscore):
  - `engines/strategy_engine.py` – `StrategyEngine` (Kombination, Validierung,
    optionaler Cache) + `load_strategy_rules`.
  - `engines/strategy_registry.py` – `StrategyRegistry` (einzige
    Erweiterungsstelle) + `build_default_registry`.
  - `engines/strategy_result.py` – `StrategyReport` (Aggregat); re-exportiert
    `StrategyResult`/`StrategyDirection` aus `strategies.base`.
  - `engines/strategy_cache.py` – `StrategyCache` (FIFO).
- **5 unabhängige Strategien** in `strategies/` (je eigene Datei):
  `fvg_strategy`, `trend_following`, `momentum_strategy`, `breakout_strategy`,
  `mean_reversion`. Gemeinsame Schnittstelle, Ergebnistypen (`StrategyResult`,
  `StrategyContext`, `StrategyEvaluation`) und Hilfen in `strategies/base.py`;
  keine Strategie hängt von einer anderen ab.
- **StrategyResult** trägt Strategy Name, Hypothesis ID, Richtung, Confidence,
  Strength, Matched Indicators/Patterns, Reasons, Warnings, Metadata (inkl.
  Hypothesentext) und Timestamp.
- **Konfiguration:** `knowledge/strategy_rules.toml` mit Parametern aller
  Strategien.
- **Validierung:** fehlende/ungültige Daten, fehlende Indikatoren, fehlende
  Muster, inkonsistente Ergebnisse.
- **Tests:** von 197 auf 247 erhöht (je Strategie, Registry, Cache, Engine).
  Testabdeckung der Strategy-Module 96 %.

### Qualitätsprüfung

Import-Zyklen: 0. Strategie-Unabhängigkeit: 0 Verstöße. SOLID-Heuristik:
0 Verstöße. Details in `HANDOVER.md`.

### Hinweis

Bewusst nicht enthalten: Score-, Risk- und Recommendation-Engine sowie
Dashboard-Logik. Die Strategy Engine erzeugt ausschließlich Hypothesen.

## [0.5.0] – 2026-07-08 – Sprint 5: Pattern Engine

### Hinzugefügt

- **Pattern Engine** (erkennt Muster, keine Entscheidungen/Scores/Signale):
  - `engines/pattern_engine.py` – `PatternEngine` (Orchestrierung, Validierung,
    optionaler Cache) + `load_pattern_rules`.
  - `engines/pattern_registry.py` – `PatternRegistry` (einzige
    Erweiterungsstelle) + `build_default_registry`.
  - `engines/pattern_result.py` – `PatternReport` (Aggregat); re-exportiert
    `PatternResult`/`PatternType`/`PatternDirection` aus `patterns.base`.
  - `engines/pattern_cache.py` – `PatternCache` (FIFO).
- **11 unabhängige Muster** in `patterns/` (je eigene Datei):
  - Implementiert: `fvg` (bullish/bearish, fresh/partially/mitigated, Gap-Größe
    & -%), `bos`, `choch`, `equal_highs`, `equal_lows`, `liquidity_sweep`,
    `market_structure`, `trend_structure` (HH/HL/LH/LL + Trend).
  - Vorbereitet (ohne Erkennung): `order_block`, `breaker_block`,
    `mitigation_block`.
  - Gemeinsame Schnittstelle, Ergebnistypen und Hilfen (Swing-/Struktur-Break-
    Erkennung) in `patterns/base.py`; kein Muster hängt von einem anderen ab.
- **Konfiguration:** `knowledge/pattern_rules.toml` mit Parametern aller Muster.
- **Validierung:** genug Kerzen, ungültige Muster, überlappende Muster,
  ungültige Zeitreihen, NaN.
- **Tests:** von 148 auf 197 erhöht (je Muster, Registry, Cache, Engine).
  Testabdeckung der Pattern-Module 95 %.

### Qualitätsprüfung

Import-Zyklen: 0. Muster-Unabhängigkeit: 0 Verstöße. SOLID-Heuristik:
0 Verstöße. Details in `HANDOVER.md`.

### Hinweis

Bewusst nicht enthalten: Strategy-, Score-, Risk- und Recommendation-Engine
sowie Dashboard-Logik.

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
