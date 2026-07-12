# Projektstatus

_Wird nach jedem Sprint automatisch aktualisiert._

- **Datum:** 2026-07-12
- **Aktueller Sprint:** Sprint 17 – Production Backend & Mobile API Platform
- **Status:** ✅ Abgeschlossen (endgültiges Backend; Sprint 18 = nur Android-App)

## Was ist vorhanden

### Fundament (Sprint 1)

- Struktur, Konfiguration, Logging, Fehlerklassen, Wissensbasis, Basistests.

### Data Layer (Sprint 2)

- Provider, Repository, MarketDataEngine, Cache, Validator, Universen.

### Scanner Core (Sprint 3)

- ScanRequest/ScanResult/ScanReport, ScanStatistics, ScanPipeline,
  ScannerEngine, ScannerManager.

### Indicator Engine (Sprint 4)

- 11 unabhängige Indikatoren, Registry, Engine, Result, Cache.

### Pattern Engine (Sprint 5)

- 11 Muster (8 implementiert, 3 vorbereitet), Registry, Engine, Result, Cache.

### Strategy Engine (Sprint 6)

- 5 Strategien, Registry, Engine, Result, Cache (nur Hypothesen).

### Score Engine (Sprint 7)

- **5 Score-Modelle** in `scores/` (je eigene Datei): `weighted_score`,
  `confidence_score`, `quality_score`, `consensus_score`, `market_score`.
- **8 Komponenten** (separat gespeichert): Trend, Momentum, Pattern Strength,
  Pattern Confidence, Indicator Quality, Market Context, Volume Quality,
  Data Quality.
- **ScoreResult**: Score ID, Strategy Name, Hypothesis ID, Total Score (0-100),
  Confidence (0-1), Quality/Consensus/Market Score, Component Scores, Reasons,
  Warnings, Metadata, Timestamp.
- **Transparenz**: jeder Score über Komponenten erklärbar (z. B. `trend: 18/20`).
- **ScoreEngine**: Input `StrategyReport` (+ Indikatoren/Muster für Komponenten)
  → `ScoreReport`.
- **Registry** (`ScoreRegistry`) als einzige Erweiterungsstelle.
- **Cache** (`ScoreCache`, FIFO).
- **Validierung**: fehlende Hypothesen, ungültige Gewichte, Gewichte ≠ 100 %,
  fehlende Komponenten.
- **Gewichte** ausschließlich aus `knowledge/score_rules.toml`.
- **Tests:** 307 gesamt (60 neue).

### Architecture Consolidation (Sprint 7.5)

Verhaltenserhaltender Umbau (kein neues Feature):

- **Entities-Schicht `models/`** bündelt alle Ergebnis-/Datentypen
  (`market`, `indicator`, `pattern`, `strategy`, `score`; `risk`/
  `recommendation` vorbereitet). Alte Importpfade bleiben als Re-Exports gültig.
- **Alle Ergebnisobjekte sind unveränderlich** (`frozen`); Engines konstruieren
  einmalig am Ende und nutzen `dataclasses.replace()` für die Rechenzeit.
- **Generische `Cache[T]`/`Registry[T]`** in `core/`; die Engine-Varianten sind
  dünne Spezialisierungen. **Einheitliche Exception-Hierarchie** unter
  `AlphaAIError`.
- **Kopplung reduziert:** `strategies`/`scores` importieren nichts mehr aus
  `engines`. Prüfskript `scripts/quality_check.py` fest im Test verankert.
- **Tests:** 335 gesamt (28 neue; bestehende unverändert).

### Risk Engine (Sprint 8)

- **8 unabhängige Risk-Modelle** in `risk/` (je eigene Datei): `position_sizing`,
  `volatility_risk`, `liquidity_risk`, `gap_risk`, `market_risk`,
  `correlation_risk`, `portfolio_risk`, `execution_risk`. Gemeinsame
  Schnittstelle/Helfer in `risk/base.py`; kein Modell hängt von einem anderen ab.
- **10 Risikokomponenten** (getrennt, erklärbar): Volatilität, Liquidität, Gap,
  Spread, ATR, Markt, Korrelation, Portfolio-Exposure, Datenqualität, News
  (News vorbereitet/neutral).
- **RiskResult** mit Overall Risk (0-100), Risk Level (LOW/MEDIUM/HIGH),
  Positionsgröße, Stückzahl/Orderwert/Slippage/Kommission, Stop-/Take-Profit-
  Abstand, CRV, Komponenten, Reasons/Warnings.
- **RiskEngine**: Input `ScoreReport` (+ Indikatoren/Rohdaten) → `RiskReport`.
  `RiskRegistry` (einzige Erweiterungsstelle), `RiskCache` (FIFO).
- **Positionsgröße** aus `settings.toml` (Depot, Fractional Shares, Risiko/Trade,
  max. Positionen); Ausführungskosten/Schwellen aus `knowledge/risk_rules.toml`.
- **Portfolio-Risiko vorbereitet** (offene Positionen werden durchgereicht).
- **Validierung**: fehlende Scores, negative Depotgröße, ungültige ATR/Preise,
  ungültige Positionsgrößen/Risk-Reward.
- **Tests:** 413 gesamt (76 neue).

### Recommendation Engine (Sprint 9)

- **5 unabhängige Modelle** in `recommendation/` (je eigene Datei):
  `decision_model`, `recommendation_model`, `confidence_model`, `summary_model`,
  `explanation_model`. Gemeinsame Logik in `recommendation/base.py`.
- **6 Entscheidungsfaktoren** (Strategie, Score, Risiko, Konsens, Marktqualität,
  Datenqualität) → Gesamtrating 0-100 → **Stärke** (VERY_HIGH/HIGH/MEDIUM/LOW/
  REJECT) + **Richtung** (LONG/SHORT/NEUTRAL, getrennt seit 9.6) + Handlung
  (OPEN/WAIT/MONITOR/SKIP).
- **No-Trade-Philosophie:** Der Score-Anteil ist begrenzt, Konsens belohnt
  Breite, und Gates deckeln bei Risiko/geringem Konsens/schwacher Datenqualität
  – ein hoher Score allein führt nie zu BUY. `WAIT`/`AVOID` sind vollwertig.
- **RecommendationEngine**: Input `StrategyReport` + `ScoreReport` +
  `RiskReport` → `RecommendationReport`. `RecommendationRegistry` (einzige
  Erweiterungsstelle), `RecommendationCache` (FIFO).
- **Erklärbarkeit:** jede Empfehlung mit Reasons, Warnings, Summary – keine
  Blackbox. Regeln ausschließlich aus `knowledge/recommendation_rules.toml`.
- **Validierung:** fehlender/ungültiger Strategy-/Score-/Risk-Report, fehlende
  Zuordnung, ungültige Level/Confidence/Ratings.
- **Tests:** 502 gesamt (89 neue).

### End-to-End-Integration (Sprint 9.5)

- **IntegrationRunner** (`pipeline/runner.py`) verkettet die komplette Pipeline
  `MarketData → Indicator → Pattern → Strategy → Score → Risk → Recommendation`.
  Keine neue Fachlogik, keine Umgehung von Schichten.
- **PipelineResult** (`models/pipeline.py`, `frozen`) bündelt alle Stufen.
- **Konsistenzprüfung** (`pipeline/consistency.py`): jede Empfehlung → genau ein
  Risk → genau ein Score → genau eine Strategie; IDs eindeutig, Referenzen gültig.
- **13 echte Szenarien** + **180 Integrations-Tests** (kein Mock): 0
  Konsistenzverstöße, alle Entscheidungs-Invarianten bestätigt.
- **Reports:** `docs/PIPELINE.md`, `docs/VALIDATION_REPORT.md` (mit
  Auffälligkeiten und Verbesserungsvorschlägen; keine Engine geändert).
- **Tests:** 682 gesamt (180 neue).

### Recommendation Semantics (Sprint 9.6)

- **Richtung und Qualität getrennt:** `RecommendationResult` trägt `direction`
  (LONG/SHORT/NEUTRAL) **und** `recommendation_strength` (VERY_HIGH … REJECT).
  Die Stärke impliziert nie mehr BUY/SELL/LONG/SHORT.
- Der 9.5-Befund „bärisches Setup → STRONG_BUY" ist **behoben**
  (`trend_down` → SHORT/VERY_HIGH). Bewertungslogik unverändert (Ratings
  identisch), nur Semantik/Benennung.
- **Tests:** 713 gesamt.

### Historical Backtesting Framework (Sprint 10)

- **Rein bewertend:** historische Marktdaten laufen durch die **bestehende**
  Pipeline; das Framework misst, wie sich die daraus entstehenden Empfehlungen
  entwickelt hätten. **Keine** neue Handelsregel, **keine** Änderung an einer
  Engine, **keine** echte Order (nur Simulation).
- **Subsystem `backtesting/`:** `historical_runner` (fensterweise, **kein**
  Look-Ahead), `trade_simulator` (Entry/Exit/Stop/Take-Profit, Fractional Shares,
  Kosten, eine Position zur Zeit, Stop hat bei Doppel-Treffer Vorrang),
  `performance_metrics`, `equity_curve`, `statistics` (Sharpe/Sortino/Calmar
  **vorbereitet**), `benchmark` (Buy & Hold), `base` + 4 Modelle.
- **Engine-Anbindung:** `BacktestEngine` (Input `MarketResult`/DataFrame →
  `BacktestReport`/`BacktestResult`), `BacktestRegistry` (einzige
  Erweiterungsstelle), `BacktestCache` (FIFO), Re-Export `backtest_result`.
- **BacktestResult:** ID, Symbol, Timeframe, Start/Ende, Anzahl Signale/Trades,
  Win/Loss Rate, Profit Factor, Ø Gewinn/Verlust, Ø CRV, Ø Haltedauer, Max
  Drawdown, Expectancy, Sharpe/Sortino/Calmar (vorbereitet), Equity Curve,
  Trade-Liste, Benchmark, Summary, Metadata, Timestamp. Jeder Trade ist
  vollständig nachvollziehbar.
- **Config:** Parameter aus `knowledge/backtest_rules.toml`; Konto-/Risikowerte
  ausschließlich aus `config/settings.toml`. **Validierung:** Zeitraum, Daten,
  leere Historie, Preise, Kennzahlen.
- **Tests:** 868 gesamt (155 neue).

### Paper Trading Framework (Sprint 11)

- **Rein bewertend:** die bestehende Pipeline erzeugt täglich Empfehlungen; ein
  **simuliertes** Portfolio eröffnet/bewertet/schließt daraus Positionen.
  **Niemals** echte Orders, **keine** Broker-API, **keine** neue Handelsregel,
  **keine** Änderung an Pipeline oder Backtesting.
- **Subsystem `paper_trading/`:** `paper_runner` (tagweise, **kein** Look-Ahead),
  `portfolio` (Validierung, Kapital/Drawdown/Exposure), `position`
  (Mark-to-Market, Stop/Take-Profit, Trailing Stop **vorbereitet**), `order`
  (OPEN/CLOSE/CANCEL/EXPIRE), `trade`, `journal`, `statistics`, `performance`,
  `base` + zwei Modelle.
- **Engine-Anbindung:** `PaperTradingEngine` (Input `MarketResult`/DataFrame →
  `PaperTradingReport`), `PaperTradingRegistry` (einzige Erweiterungsstelle),
  `PaperTradingCache` (FIFO), Re-Export `paper_trading_result`.
- **PaperTradingResult:** ID, Recommendation-ID, Direction, Recommendation
  Strength, Entry/Current/Exit, Position Size, (Fractional) Shares, Status
  (OPEN/CLOSED/CANCELLED), Entry/Exit Time, PnL €/%, Running/Max Drawdown,
  Current Equity, Portfolio Exposure, Reasons, Warnings, Metadata, Timestamp.
- **Config:** Parameter aus `knowledge/paper_trading_rules.toml`; Konto-/Risiko-
  werte ausschließlich aus `config/settings.toml`. **Validierung:** doppelte
  Position, Größen, Preise, Zeitstempel, Statuswechsel.
- **Tests:** 1045 gesamt (177 neue).

### Trading Intelligence & Analytics Framework (Sprint 12)

- **Rein auswertend:** analysiert **ausschließlich** bestehende Backtest-/Paper-
  Trading-Ergebnisse und erzeugt objektive, reproduzierbare Statistiken.
  **Keine** Bewertung von Trades, **keine** Handelsentscheidung, **keine**
  Änderung bestehender Ergebnisse, **keine** neuen Empfehlungen, **keine** ML.
- **Subsystem `analytics/`:** `aggregation` (Kennzahl-Bausteine), `labeling`
  (Strategie/Risiko/Score aus `recommendation_id`/`reasons`), `normalization`
  (Trades → `AnalyticsTrade`), zehn unabhängige Modelle (`trade_statistics`,
  `performance_analyzer`, `pattern_analysis`, `strategy_analysis`,
  `recommendation_analysis`, `risk_analysis`, `market_analysis`, `time_analysis`,
  `journal_analysis`, `summary_analysis`), `base`.
- **Engine-Anbindung:** `AnalyticsEngine` (Input `BacktestReport` +
  `PaperTradingReport` → `AnalyticsReport`), `AnalyticsRegistry` (einzige
  Erweiterungsstelle; die Engine bleibt für neue Modelle unverändert),
  `AnalyticsCache` (FIFO), Re-Export `analytics_result`.
- **AnalyticsResult:** Analytics-/Backtest-/PaperTrading-ID, Trade Count, Win/
  Loss Rate, Profit Factor, Expectancy, Ø Winner/Loser, Max Drawdown, Ø Haltedauer,
  Ø CRV, Long/Short/Strategy/Pattern/Recommendation/Risk/Market/Time/Journal
  Statistics, Performance, Summary, Warnings, Metadata, Timestamp – dashboard-fertig.
- **Config:** Parameter aus `knowledge/analytics_rules.toml`. **Validierung:**
  leere Reports, fehlende Trades, ungültige Parameter/Kennzahlen.
- **Tests:** 1229 gesamt (184 neue).

### AlphaAI Command Center / Dashboard (Sprint 13)

- **Rein darstellend:** ausschließlich Presentation Layer. **Berechnet niemals**
  Daten, enthält **keinerlei** Geschäftslogik und erzeugt **keine** Scores/
  Risiken/Empfehlungen/Analysen/Kennzahlen. Alle Werte stammen einzig aus den
  bestehenden Reports; fehlt ein Wert, wird nur ein Platzhalter angezeigt.
- **Entities:** `models/dashboard.py` (`MetricCard`, `StatusItem`, `ChartSeries`,
  `ChartSpec`, `TableSpec`, `WidgetSpec`, `DashboardView`, alle `frozen`).
- **Paket `dashboard/`:** `theme` (einzige Quelle des Aussehens, Dark Carbon),
  `state` (Snapshot/Restore – Zustand geht nie verloren), `format`, `charts`,
  `status`, `settings`(+`settings.toml`, nur Anzeigeoptionen), `viewmodels`
  (lesen Reports ab), `responsive`, `feedback`, `engine` (bleibt für neue
  Widgets/Seiten unverändert), `render`/`app` (einzige Streamlit-Schicht).
- **Widget-System:** 26 unabhängige Widgets, `widget_registry` (einzige
  Registrierungsstelle), `router` (9 Seiten + Tastenkürzel).
- **Zustände:** Ladezustände (Skeleton/Progress/Fade), Fehlerzustände (offline/
  no_data/…), Responsive (Desktop/Tablet/UltraWide/4K), Auto-Refresh (lädt nur
  Reports). Keine Exceptions im Frontend.
- **Tests:** 1488 gesamt (259 neue).

### Market Intelligence Framework (Sprint 14)

- **Rein priorisierend:** bewertet **ausschließlich** bereits vorhandene
  Ergebnisse (Empfehlung, Risiko, Analytics, Backtesting, Paper Trading) und
  ordnet daraus die objektiv besten Chancen. **Keine** neue Handelsregel,
  **keine** Veränderung bestehender Ergebnisse, **kein** Broker, **kein** ML.
- **Entities:** `models/opportunity.py` (`MarketCandidate`, `Opportunity`,
  `OpportunityReport`, `OpportunityStatistics`, `OpportunityExplanation`,
  `Watchlist`, `OpportunityModelOutput`, `MarketIntelligenceContext`; alle `frozen`).
- **Subsystem `market_intelligence/`:** `base`, `opportunity` (fünf
  Bewertungsmodelle + `build_opportunity`), `ranking`, `ranking_engine`,
  `filter`, `explainer`, `statistics`, `cache`.
- **Engine-Anbindung:** `MarketIntelligenceEngine` (Input vier Reports je Aktie →
  `OpportunityReport`), `MarketIntelligenceRegistry` (einzige Erweiterungsstelle),
  `OpportunityCache` (FIFO), Re-Export `market_intelligence_result`.
- **Opportunity Score:** gewichtete Zusammenfassung (Recommendation 0.40, Risk
  0.20, Analytics 0.15, Backtest 0.15, Paper Trading 0.10) – kein neues
  Bewertungssystem; Gewichte aus `knowledge/market_intelligence_rules.toml`.
- **Ranking/Filter/Sortierung/Explainer/Statistik/Watchlists** vollständig;
  neue Dashboard-Seite „Market Intelligence" (additiv, Engine unverändert).
- **Validierung:** leere/ungültige Reports, doppelte Ticker, ungültige Gewichte/
  Scores. **Tests:** 1690 gesamt (201 neue).

### Market Discovery Framework (Sprint 15)

- **Von Watchlists unabhängig:** durchsucht den gesamten konfigurierten Markt
  selbstständig, filtert ungeeignete Werte **vor** der vollständigen Analyse und
  priorisiert die besten Chancen. Der Benutzer gibt keine Aktien mehr vor.
  **Berechnet niemals** Indikatoren/Muster/Strategien/Scores/Risiken/Empfehlungen.
- **Entities:** `models/market_discovery.py` (`MarketDefinition`, `MarketSymbol`,
  `MarketUniverse`, `CandidateAnalysis`, `RejectedCandidate`,
  `DiscoveryOpportunity`, `DiscoveryStatistics`, `DiscoveryReport`; alle `frozen`).
- **Subsystem `market_discovery/`:** `universe_loader`, `market_universe`,
  `candidate_filter`, `candidate`, `sector_balancer`, `market_statistics`,
  `discovery_engine`, `discovery_cache`. Importiert nur `models`/`core`; Pipeline-
  Ergebnisse und Market-Intelligence werden **injiziert**.
- **Engine-Anbindung:** `MarketDiscoveryEngine` (lädt Universum → Vorfilter →
  Intelligence → Ausgleich → Report), `MarketDiscoveryRegistry` (10 Märkte,
  einzige Erweiterungsstelle), `DiscoveryCache` (FIFO), Re-Export
  `market_discovery_result`.
- **Vorfilter** (Grenzwerte aus `market_discovery_rules.toml`), **Branchen-
  Ausgleich** (konfigurierbar, keine festen Limits), neue Dashboard-Seite
  „Market Discovery" (additiv; Engine unverändert).
- **Validierung:** leeres Universum, unbekannte Märkte, ungültige/doppelte
  Kandidaten. **Tests:** 1836 gesamt (145 neue).

### Live Market Operations Platform (Sprint 16)

- **Produktives Tagessystem:** der Benutzer startet AlphaAI, danach laufen alle
  Marktanalysen automatisch (keine manuellen Discovery-/Scanner-Läufe). **Niemals**
  Orders; **keine** Handelsentscheidung; **keine** Berechnung von
  Indikatoren/Mustern/Strategien/Scores/Risiken/Empfehlungen – nur Orchestrierung.
- **Entities:** `models/operations.py` (`MarketState`, `MarketClock`, `JobRun`,
  `ScheduledJob`, `JobDefinition`, `Heartbeat`, `SystemState`, `OperationReport`;
  alle `frozen`, UI-unabhängig).
- **Subsystem `operations/`:** `market_sessions`, `market_clock` (Sommer-/
  Winterzeit über IANA-Zeitzonen), `scheduler`, `job_queue` (ein Discovery
  gleichzeitig), `job_runner` (Fehlerisolation), `job_history`, `heartbeat`,
  `health`, `system_state`. Importiert nur `models`/`core`; Jobs + Uhr injiziert.
- **Engine-Anbindung:** `OperationsEngine` (`tick()`/`build_report()`),
  `OperationsRegistry` (7 Job-Arten), `OperationsCache`, Re-Export
  `operations_result`. Regeln aus `knowledge/operations_rules.toml`.
- **Market Clock** (offene/geschlossene Börsen, nächste Öffnung, Countdown),
  automatische Jobs/Scan-Strategie, neue Dashboard-Seite „Live Operations".
- **Validierung:** ungültige Marktzeiten/Zeitzonen, doppelte Jobs, Job-Absturz,
  Queue-Exklusivität. **Tests:** 2040 gesamt (203 neue).

### Production Backend & Mobile API Platform (Sprint 17)

- **Produktiver Backend-Dienst:** AlphaAI läuft als Dienst; alle Reports werden
  automatisch erzeugt und **dauerhaft gespeichert** (SQLite). Eine
  produktionsreife **REST-API** liefert sämtliche Informationen als JSON. Die
  API/das Backend **berechnen nichts**, erzeugen **keine** Scores/Empfehlungen und
  treffen **keine** Handelsentscheidung – reine Auslieferung vorhandener Reports.
- **Entities:** `models/application.py` (`ApiVersion`, `ServiceInfo`,
  `ComponentHealth`, `HealthReport`, `StoredReport`, `ApiError`, `ApiEnvelope`,
  `EndpointInfo`; alle `frozen`; Enums `HealthStatus`, `ReportKind`).
- **Schicht `application/`:** `exceptions`, `serialization` (generischer
  JSON-Serialisierer), `repositories` (`ReportStore`/SQLite), `responses`
  (Envelope), `services` (`ReportService`, `SystemService`, `BackgroundService`),
  `health` (`HealthMonitor`), `authentication` (`LocalOnlyPolicy`), `api`
  (framework-unabhängiger Router + FastAPI-Adapter). Importiert nur
  `models`/`core`; Pipeline injiziert.
- **Engine-Anbindung:** `ApplicationEngine` (Composition Root),
  `ApplicationRegistry` (Report-Arten), `ApplicationCache`, `application_result`.
  Regeln aus `knowledge/application_rules.toml`.
- **REST-API (`/api/v1`, JSON):** System/Märkte/Empfehlungen/Analytics/Dashboard
  (17 Endpunkte). Einheitliches Envelope, Versionierung, revisionsgebundener
  Cache, GZip, Zugriff vorerst nur lokal.
- **Robustheit:** automatische Recovery (Fehler stoppen den Dienst nie dauerhaft);
  Neustart verliert keine Daten; immer der letzte erfolgreiche Scan.
- **Validierung:** ungültige Requests/Parameter, leere/fehlende Reports,
  Scheduler-/Persistenz-/API-Fehler. **Tests:** 2294 gesamt (254 neue).

## Was ist bewusst NICHT vorhanden

- Keine Dashboard-**Berechnung** (das Dashboard zeigt nur an), keine Broker-API,
  keine automatische Orderausführung, **keine echten Orders**.
- Backtesting und Paper Trading **simulieren** ausschließlich; sie eröffnen
  keine echte Position und senden keine Order. Die Recommendation Engine liefert
  ausschließlich `RecommendationResult`.

Diese Teile folgen in späteren Sprints (siehe `ROADMAP.md`).

## Qualitätsnachweis (Sprint 17)

| Prüfung | Ergebnis |
|---|---|
| pytest | 2294 Tests bestanden |
| Ruff / Black | konform |
| Import-Zyklen | 0 |
| Entities-Schicht `models/` | 0 Verstöße |
| Plugin-Unabhängigkeit | 0 Verstöße |
| SOLID-Heuristik | 0 Verstöße |
| Pipeline-Konsistenz | 0 Verstöße |
| Ergebnisobjekte unveränderlich (`frozen`) | vollständig |

## Nächster Schritt

Warten auf Freigabe für den nächsten Sprint. Priorisiert: perspektivisch das
**Dashboard**, das die fertigen Kennzahlen aus dem `AnalyticsResult` **nur
visualisiert** (keine Geschäftslogik); daneben **Kalibrierung** an realen Daten
(Schwellen/Gewichte der Empfehlung, Annualisierung der vorbereiteten
Backtest-Kennzahlen, Aktivierung des vorbereiteten Trailing Stops). Weiterhin
ohne automatische Orderausführung und ohne Broker-API.
