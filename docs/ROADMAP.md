# Roadmap

_Wird laufend gepflegt._ Die Roadmap zeigt die geplante Reihenfolge der
Sprints. Jeder Sprint baut auf dem vorherigen auf und endet mit aktualisierter
Dokumentation.

## Sprint 1 – Fundament ✅ (abgeschlossen)

Projektstruktur, Konfiguration, Logging, Fehlerklassen, Wissensbasis,
Dokumentation, Basistests. Kein Scanner, keine Daten, keine Handelslogik.

## Sprint 2 – Data Layer ✅ (abgeschlossen)

- Einheitliche Provider-Schnittstelle (`BaseProvider`) und `YahooProvider`.
- Weitere Provider vorbereitet (Finnhub, Polygon, AlphaVantage, IEX).
- `MarketRequest`/`MarketResult` mit kanonischem OHLCV-Schema.
- `MarketRepository` (Provider + Cache + Validator) und `MarketDataEngine`.
- `TTLCache` mit kategoriespezifischer TTL; Validator für Datenqualität.
- Universen (DAX/MDAX/SDAX/TecDAX, S&P 500/Nasdaq-100/Russell 2000, ETF
  vorbereitet) aus `config/universe.toml`.
- 68 Tests. Kein Scanner, keine Indikatoren, keine Handelslogik.

## Sprint 3 – Scanner Core ✅ (abgeschlossen)

- `ScanRequest`/`ScanResult`/`ScanReport` und `ScanStatistics`.
- `ScanPipeline` (reine Orchestrierung), `ScannerEngine` (kennt nur die
  Pipeline), `ScannerManager` (Mehrfach-Scans, sequenziell).
- Cache-Statistik über `metadata["cache_hit"]`; neuer `[scanner]`-Config-Bereich.
- 27 neue Tests (95 gesamt). Keine Indikatoren, Muster, Scores oder Signale.

## Sprint 4 – Indicator Engine ✅ (abgeschlossen)

- 11 unabhängige Indikatoren in `indicators/` (je eigene Datei).
- `IndicatorRegistry` (einzige Erweiterungsstelle), `IndicatorEngine`,
  `IndicatorResult`, `IndicatorCache`.
- Parameter aus `knowledge/indicator_rules.toml`; Multi-Timeframe vorbereitet.
- 53 neue Tests (148 gesamt), Testabdeckung neuer Module 92 %.
- Keine Muster, keine Scores, keine Signale.

## Sprint 5 – Pattern Engine ✅ (abgeschlossen)

- 11 unabhängige Muster in `patterns/` (8 implementiert, 3 vorbereitet).
- `PatternRegistry` (einzige Erweiterungsstelle), `PatternEngine`,
  `PatternResult`/`PatternReport`, `PatternCache`.
- Parameter aus `knowledge/pattern_rules.toml`.
- 49 neue Tests (197 gesamt), Testabdeckung Pattern-Module 95 %.
- Keine Scores, keine Signale, keine Handelsentscheidungen.

## Sprint 6 – Strategy Engine ✅ (abgeschlossen)

- 5 unabhängige Strategien in `strategies/` (FVG, Trend Following, Momentum,
  Breakout, Mean Reversion), die Indikatoren und Muster zu Hypothesen
  kombinieren.
- `StrategyRegistry` (einzige Erweiterungsstelle), `StrategyEngine`,
  `StrategyResult`/`StrategyReport`, `StrategyCache`.
- Parameter aus `knowledge/strategy_rules.toml`.
- 50 neue Tests (247 gesamt), Testabdeckung Strategy-Module 96 %.
- Nur Hypothesen; keine Scores, keine Kauf-/Verkaufsentscheidung.

## Sprint 7 – Score Engine ✅ (abgeschlossen)

- 5 unabhängige Score-Modelle in `scores/` (weighted, confidence, quality,
  consensus, market) und 8 separat gespeicherte Komponenten.
- `ScoreRegistry` (einzige Erweiterungsstelle), `ScoreEngine`,
  `ScoreResult`/`ScoreReport`, `ScoreCache`.
- Vollständig transparente Scores (Komponenten-Aufschlüsselung).
- Gewichte aus `knowledge/score_rules.toml`.
- 60 neue Tests (307 gesamt), Testabdeckung Score-Module 96 %.
- Nur Scores; keine Entscheidung, keine Positionsgröße, kein Risiko.

## Sprint 7.5 – Architecture Consolidation ✅ (abgeschlossen)

Verhaltenserhaltender Umbau vor den nächsten Fachschichten (kein neues Feature):

- Domänenmodelle in der Entities-Schicht `models/` konsolidiert (alte Pfade als
  Re-Exports), `strategies`/`scores` entkoppelt von `engines`.
- Alle Ergebnisobjekte unveränderlich (`frozen`); Engines konstruieren einmalig.
- Generische `Cache[T]`/`Registry[T]` und einheitliche Exception-Hierarchie in
  `core/`.
- Prüfskript `scripts/quality_check.py` fest im Test verankert.
- 335 Tests (28 neue), Tag `v0.1.0-foundation`.

## Sprint 8 – Risk Engine ✅ (abgeschlossen)

- Kette `ScoreReport → RiskEngine → RiskReport`; nur Risikobewertung und
  Positionsgrößen-Empfehlung, keine Handelsentscheidung/Order.
- 8 unabhängige Risk-Modelle in `risk/` (position_sizing, volatility, liquidity,
  gap, market, correlation, portfolio, execution); 10 erklärbare Komponenten.
- `RiskRegistry` (einzige Erweiterungsstelle), `RiskEngine`,
  `RiskResult`/`RiskReport`, `RiskCache`.
- Positionsgröße aus `settings.toml`, übrige Parameter aus
  `knowledge/risk_rules.toml`. Portfolio-Risiko vorbereitet (offene Positionen
  werden durchgereicht).
- 76 neue Tests (413 gesamt). News-Risiko vorbereitet (neutral).

## Sprint 9 – Recommendation Engine ✅ (abgeschlossen)

- Kette `Strategy+Score+Risk → RecommendationEngine → RecommendationReport`;
  letzte fachliche Entscheidungsschicht, keine Order/Broker-Anbindung.
- 5 unabhängige Modelle in `recommendation/` (decision, recommendation,
  confidence, summary, explanation); 6 Entscheidungsfaktoren.
- Stufen STRONG_BUY/BUY/WATCH/WAIT/AVOID + Handlungen OPEN/WAIT/MONITOR/SKIP.
- No-Trade-Philosophie mit Gates: hoher Score allein führt nie zu BUY; WAIT/
  AVOID sind vollwertig. Vollständige Erklärbarkeit (Reasons/Warnings/Summary).
- `RecommendationRegistry`, `RecommendationCache`, Regeln aus
  `knowledge/recommendation_rules.toml`. 89 neue Tests (502 gesamt).

## Sprint 9.5 – End-to-End Integration & Validation ✅ (abgeschlossen)

- `IntegrationRunner` verkettet die komplette Pipeline (Data → Indicator →
  Pattern → Strategy → Score → Risk → Recommendation); keine neue Fachlogik.
- `PipelineResult` (frozen) + `verify_pipeline` (Referenz-/Eindeutigkeits-
  Konsistenz). 13 echte Szenarien, 180 Integrations-Tests, 0 Verstöße.
- Reports `docs/PIPELINE.md` und `docs/VALIDATION_REPORT.md` (inkl.
  Auffälligkeiten und Verbesserungsvorschlägen). 682 Tests gesamt.

## Sprint 9.6 – Recommendation Semantics ✅ (abgeschlossen)

- Reiner Semantik-Sprint: Trennung von **Richtung** (`Direction`
  LONG/SHORT/NEUTRAL) und **Stärke** (`RecommendationStrength`
  VERY_HIGH … REJECT) in `RecommendationResult`. Keine neue Logik/Regel.
- 9.5-Befund „bärisches Setup → STRONG_BUY" behoben; die Stärke enthält nie
  mehr BUY/SELL/LONG/SHORT. Bewertungslogik/Ratings unverändert.
- Alle Recommendation-/Integrationstests umgestellt + neue LONG/SHORT/NEUTRAL-
  Tests. 713 Tests gesamt. `VALIDATION_REPORT.md` aktualisiert.

## Sprint 10 – Historical Backtesting Framework ✅ (abgeschlossen)

- Kette `Historische Marktdaten → bestehende Pipeline → BacktestEngine →
  BacktestReport`; **rein bewertend**, keine neue Handelsregel, keine Änderung an
  einer bestehenden Engine, keine echte Order (nur Simulation).
- Subsystem `backtesting/` (`historical_runner`, `trade_simulator`,
  `performance_metrics`, `equity_curve`, `statistics`, `benchmark`, `base` + vier
  Modelle) und Engine-Anbindung (`backtest_engine`, `backtest_registry`,
  `backtest_cache`, `backtest_result`).
- `BacktestResult` mit allen geforderten Kennzahlen (Win/Loss Rate, Profit
  Factor, Expectancy, Max Drawdown, Ø CRV/Haltedauer, Sharpe/Sortino/Calmar
  vorbereitet, Equity Curve, Trade-Liste, Benchmark, Summary, Metadata).
- Fractional Shares; Konto-/Risikowerte ausschließlich aus `settings.toml`;
  Parameter aus `knowledge/backtest_rules.toml`. Buy-&-Hold-Benchmark.
  Validierung (Zeitraum/Daten/Preise/Kennzahlen). Kein Look-Ahead.
- 155 neue Tests (868 gesamt). Doku: `docs/BACKTESTING.md`.

## Sprint 11 – Paper Trading Framework ✅ (abgeschlossen)

- Kette `Live-Marktdaten → bestehende Pipeline → PaperTradingEngine →
  PaperPortfolio → PaperTradingReport`; **rein bewertend**, keine neue
  Handelsregel, keine Änderung an einer Engine oder am Backtesting, **niemals**
  echte Orders (nur Simulation), keine Broker-API.
- Subsystem `paper_trading/` (`paper_runner`, `portfolio`, `position`, `order`,
  `trade`, `journal`, `statistics`, `performance`, `base` + zwei Modelle) und
  Engine-Anbindung (`paper_trading_engine`, `-registry`, `-cache`, `-result`).
- `PaperTradingResult` mit allen geforderten Feldern (Status OPEN/CLOSED/
  CANCELLED, Entry/Current/Exit, PnL €/%, Running/Max Drawdown, Current Equity,
  Exposure, Direction, Recommendation Strength, Reasons/Warnings, …). Order-
  Management (OPEN/CLOSE/CANCEL/EXPIRE), automatisches Journal, Statistik.
- Fractional Shares; Konto-/Risikowerte ausschließlich aus `settings.toml`;
  Parameter aus `knowledge/paper_trading_rules.toml`. Validierung (doppelte
  Position, Größen, Preise, Zeitstempel, Statuswechsel). Trailing Stop vorbereitet.
- 177 neue Tests (1045 gesamt). Doku: `docs/PAPER_TRADING.md`.

## Sprint 12 – Trading Intelligence & Analytics Framework ✅ (abgeschlossen)

- Kette `BacktestReport + PaperTradingReport → AnalyticsEngine → AnalyticsReport`;
  **rein auswertend**, keine Bewertung, keine neue Empfehlung, keine ML, keine
  Änderung an einer Engine, am Backtesting oder am Paper Trading.
- Subsystem `analytics/` (`aggregation`, `labeling`, `normalization`, `base` +
  zehn unabhängige Analysemodelle: `trade_statistics`, `performance_analyzer`,
  `pattern_analysis`, `strategy_analysis`, `recommendation_analysis`,
  `risk_analysis`, `market_analysis`, `time_analysis`, `journal_analysis`,
  `summary_analysis`) und Engine-Anbindung (`analytics_engine`, `-registry`,
  `-cache`, `-result`).
- `AnalyticsResult` mit allen geforderten Feldern (Win/Loss Rate, Profit Factor,
  Expectancy, Max Drawdown, Long/Short/Strategy/Pattern/Recommendation/Risk/
  Market/Time/Journal Statistics, Summary, Metadata). Dimensionen
  (Strategie/Risiko/Score) reproduzierbar aus `recommendation_id`/`reasons`.
- Regeln aus `knowledge/analytics_rules.toml`; Validierung (leere Reports,
  fehlende Trades, ungültige Parameter). Kennzahlen dashboard-fertig.
- 184 neue Tests (1229 gesamt). Doku: `docs/ANALYTICS.md`.

## Sprint 6 – Dashboard (geplant)

- Streamlit-Oberfläche in `dashboard/`.
- Charts mit Plotly.
- Anzeige der Empfehlungen mit Begründung.

## Sprint 7 – Persistenz & Lernfähigkeit (geplant)

- Speicherung von Analysen/Empfehlungen in SQLite (`database/`).
- Nachkontrolle der Empfehlungen und Auswertung.
- Rückspielung der Erkenntnisse in `knowledge/journal.md`.

## Sprint 8 – API (geplant)

- FastAPI-Schnittstelle, um Analysen programmatisch abzurufen.

> Reihenfolge und Umfang können sich anpassen. Änderungen werden hier und in
> `CHANGELOG.md` dokumentiert.
