# Changelog

_Wird nach jedem Sprint automatisch aktualisiert._ Das Format orientiert sich
an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/) und
[Semantic Versioning](https://semver.org/lang/de/).

## [0.18.2] – 2026-07-14 – Echte Marktdaten (Live-Verdrahtung)

Schließt die bestehende Analyse-Pipeline an den Backend-Dienst an, ohne
bestehende Engines zu verändern. Keine neue Handelslogik.

### Hinzugefügt

- **`scripts/live_backend.py`** – Composition Root `LiveBackend`: verbindet
  Marktdaten (`MarketDataEngine`/Yahoo, Provider injizierbar) → Analyse-Pipeline
  (`IntegrationRunner`) → Market Intelligence zu einem priorisierten
  `OpportunityReport`. Reicht nur vorhandene Engine-Ausgaben weiter.
- **`scripts/serve.py --live`** (+ `--symbols`, `--universe`): startet den Dienst
  mit echten Marktdaten; der erste Takt lädt Kurse, analysiert und speichert die
  Chancen. Marktuhr über den Operations-Taktgeber.
- **Tests:** `tests/test_live_backend.py` (5) – vollständige Pipeline über einen
  synthetischen Provider (ohne Netzwerk); Gesamt 2299.

## [0.18.1] – 2026-07-14 – Lauffähigkeit: Server-Start & App-Build

Nachrüstung, damit AlphaAI ohne weitere Handgriffe **betrieben** werden kann.
Keine fachlichen Änderungen an Engines/Analyse.

### Hinzugefügt

- **`scripts/serve.py`** – Start-Skript des Backend-Dienstes: baut die
  `ApplicationEngine`, lädt optional Demo-Reports (`--demo`) und stellt die
  REST-API per uvicorn bereit (`python -m scripts.serve --demo`).
- **`RUN.md`** – Schnellstart (Backend starten + App bauen/verbinden).
- **Android build-ready:** Gradle-Wrapper (`gradlew`, `gradlew.bat`,
  `gradle/wrapper/gradle-wrapper.jar`) und adaptives Launcher-Icon
  (`mipmap-anydpi-v26/ic_launcher*`, `ic_launcher_foreground`,
  `ic_launcher_background`) ergänzt, damit der Build durchläuft.

### Behoben

- **FastAPI-Adapter** (`application/api/service.py`): Routen werden nun auf
  Starlette-Ebene (`add_route`) gemountet. Zuvor deutete FastAPI den
  `Request`-Parameter als Query-Feld (HTTP 422). Der Adapter war in Sprint 17
  ohne installiertes FastAPI nie ausgeführt worden; jetzt live gegen echte
  HTTP-Requests verifiziert (alle Endpunkte, GZip, Swagger `/docs`).

## [0.18.0] – 2026-07-12 – Sprint 18: AlphaAI Android Application (Release Candidate)

Abschluss der Kernentwicklung: die **native Android-App** wird die primäre
Benutzeroberfläche von AlphaAI. Sie **konsumiert ausschließlich die REST-API**
(`/api/v1`) und enthält **keine** Geschäftslogik, **keine** Berechnung, **keine**
Scores/Recommendation-Logik und **keine** Trading-Funktionen (Read-only, keine
Broker/Orders). **Keine Änderungen** an bestehenden Engines oder am
Application-Backend. **Alle Kauf-/Verkaufsentscheidungen trifft der Benutzer.**

### Hinzugefügt

- **Android-Projekt `android/`** (Kotlin, Jetpack Compose, Material 3, MVVM,
  Repository Pattern, StateFlow/Coroutines):
  - **Netzwerk:** Retrofit + OkHttp + kotlinx.serialization; `AlphaAiApi`
    (alle REST-Endpunkte), einheitliche `EnvelopeDto`-Hülle, zur Laufzeit
    konfigurierbare Backend-Adresse (`HostSelectionInterceptor`).
  - **Offline-Cache:** Room (`OpportunityEntity`/`SnapshotEntity`/
    `ScanHistoryEntity` + DAOs) – zeigt ohne Verbindung den letzten
    erfolgreichen Scan samt Zeitpunkt.
  - **Repositories:** `OpportunityRepository`, `MarketRepository`,
    `SystemRepository`, `HistoryRepository` (API + Cache + Offline-Fallback).
  - **Bildschirme:** Home (Marktstatus/Top-Chancen/Signale), Opportunities
    (Suche/Filter/Sortierung), Detailseite (vollständige Analyse), Markets,
    History, Settings – plus Bottom-Navigation und Detail-Route.
  - **Design:** dunkles „Carbon"-Theme mit gelber Akzentfarbe, große Karten,
    Material 3, einhandbedienbar.
  - **DI:** manueller `AppContainer` (kein Framework); ViewModels über
    `viewModelFactory`.
- **Tests (JVM/Compose):** Envelope-Serialisierung, Mapper, alle Repositories
  (inkl. Offline/Cache), alle ViewModels, State-Management, UI-Tests
  (Chancen-Karte, Bottom-Navigation) und ein **Architecture Check**
  (`ArchitectureTest`: Schichtung + Verbot von Handels-Aktionen).
- **Qualität:** ktlint- und detekt-Konfiguration (`android/.editorconfig`,
  `android/config/detekt/detekt.yml`), zentraler Versionskatalog.
- **Dokumentation:** neu `docs/ANDROID.md`, `docs/USER_GUIDE.md`,
  `docs/INSTALLATION_ANDROID.md`, `android/README.md`.

### Unverändert (bewusst)

- Keine Änderungen an Engines/Algorithmen/Backend; keine neuen Strategien/
  Pattern/Scores; **kein Broker, keine Orderausführung, keine Trading-Funktionen**.

## [0.17.0] – 2026-07-12 – Sprint 17: Production Backend & Mobile API Platform

Sprint 17 **beendet die Backend-Entwicklung**: AlphaAI läuft ab hier als
**produktiver Backend-Dienst**. Alle Reports werden automatisch erzeugt und
**dauerhaft gespeichert**; eine produktionsreife **REST-API** stellt sämtliche
Informationen als JSON bereit. Desktop-Dashboard und Android-App (Sprint 18)
nutzen **dieselbe API** – keine doppelte Geschäftslogik. Die API/das Backend
**berechnen nichts**, erzeugen **keine** Scores/Risiken/Empfehlungen und treffen
**keine** Handelsentscheidung; keine bestehende Engine wurde verändert. **Alle
Kauf-/Verkaufsentscheidungen trifft der Benutzer.**

### Hinzugefügt

- **Entities:** `models/application.py` (alle `frozen`): `ApiVersion`,
  `ServiceInfo`, `ComponentHealth`, `HealthReport`, `StoredReport`, `ApiError`,
  `ApiEnvelope`, `EndpointInfo` (+ Enums `HealthStatus`, `ReportKind`).
- **Application Service Layer `application/`** (importiert nur `models`/`core`;
  Pipeline wird injiziert – kein Import-Zyklus):
  - `exceptions/` – `ApplicationError` + `InvalidRequestError`,
    `ReportNotFoundError`, `ServiceUnavailableError`, `PersistenceError`,
    `AuthenticationError` (je mit stabilem `code`/`status`).
  - `serialization/` – generischer, verlustfreier JSON-Serialisierer für alle
    (frozen) Report-Modelle (Dataclass/Enum/datetime/Tupel/Mapping → JSON).
  - `repositories/` – `ReportStore` (SQLite): dauerhaft, neustartfest, mit
    Retention je Art und monotoner Revision (für Cache-Invalidierung).
  - `responses/` – einheitliche Antwort-Hüllen (`ApiEnvelope`) für Erfolg/Fehler.
  - `services/` – `ReportService` (liest/filtert Reports), `SystemService`
    (Version/Status), `BackgroundService` (Takt + Persistenz + Recovery).
  - `health/` – `HealthMonitor` (aggregiert API/Scheduler/Markt/Queue/Cache/
    System/Persistenz; Gesamtzustand = schlechtester Komponentenzustand).
  - `authentication/` – `AuthPolicy`-Vertrag, `LocalOnlyPolicy` (nur lokaler
    Host), `OpenPolicy` (Tests/Dev). Keine Cloud/Benutzer/Registrierung.
  - `api/` – **framework-unabhängige** REST-API: `Router`/`ApiRequest`/
    `ApiResponse`, `routes.py` (alle Endpunkte), `ApplicationApi` (Zugriff +
    revisionsgebundener Cache), `service.py` (dünner FastAPI-/GZip-Adapter,
    lazy import).
- **Engine-Anbindung:** `engines/application_engine.py` (Composition Root:
  verdrahtet Persistenz, Dienste, Health, API, Hintergrunddienst; Regel-Laden),
  `application_registry.py` (Registry der bekannten Report-Arten – einzige
  Erweiterungsstelle), `application_cache.py`, `application_result.py`.
- **REST-API-Endpunkte (JSON, `/api/v1`):** System (`/health`, `/status`,
  `/version`, `/scheduler`, `/operations`), Märkte (`/markets`, `/market-status`,
  `/opportunities`, `/opportunities/top`, `/opportunities/{ticker}`,
  `/discovery`), Empfehlungen (`/recommendations`, `/recommendations/{ticker}`),
  Analytics (`/analytics`, `/backtesting`, `/paper-trading`), Dashboard
  (`/dashboard`).
- **Konfiguration:** `knowledge/application_rules.toml` (Service, Persistenz,
  API, Auth-Richtlinie) – alle Betriebsparameter ausschließlich aus TOML.
- **Persistenz:** produktionsgeeignete SQLite-Datenbank
  (`database/alpha_ai_reports.db`); keine temporären Dateien, keine In-Memory-
  Lösung; Dashboard und API liefern immer den letzten erfolgreichen Scan.
- **Tests:** 254 neue Tests (Serialisierung, Persistenz, Services, Health,
  Authentifizierung, Router, API, Hintergrunddienst/Recovery, Engine,
  End-to-End) – Gesamt **2294**.
- **Dokumentation:** neu `docs/API.md`, `docs/BACKEND.md`, `docs/PRODUCTION.md`.

### Geändert

- `pyproject.toml` und `scripts/quality_check.py`: neues Paket `application`
  (inkl. Unterpakete) registriert.
- Doku aktualisiert: `ARCHITECTURE.md`, `PROJECT_STATUS.md`, `ROADMAP.md`,
  `HANDOVER.md`, `AI_CONTEXT.md`, `DECISIONS.md` (ADR-038).

### Unverändert (bewusst)

- Keine Änderungen an bestehenden Engines/Algorithmen; keine neuen Strategien/
  Pattern/Scores; keine Handelslogik; **kein Broker, keine Orderausführung**.

## [0.16.0] – 2026-07-12 – Sprint 16: Live Market Operations Platform

Neue Plattform, die AlphaAI zu einem **produktiven täglichen Analyse-System**
macht: der Benutzer startet AlphaAI, danach übernimmt das System sämtliche
Marktanalysen automatisch (keine manuellen Discovery-/Scanner-Läufe mehr). Die
Plattform führt **niemals** Orders aus, trifft **keine** Handelsentscheidung und
**berechnet keine** Indikatoren/Muster/Strategien/Scores/Risiken/Empfehlungen –
sie **orchestriert** ausschließlich die bestehende Pipeline (über injizierte
Jobs). **Alle Kauf-/Verkaufsentscheidungen trifft der Benutzer.**

### Hinzugefügt

- **Entities:** `models/operations.py` (alle unveränderlich, `frozen`):
  `MarketState`, `MarketClock`, `JobRun`, `ScheduledJob`, `JobDefinition`,
  `Heartbeat`, `SystemState`, `OperationReport` (+ Enums `JobStatus`,
  `SystemHealth`). Alle Reports sind **UI-unabhängig**.
- **Subsystem `operations/`:** `market_sessions`, `market_clock` (Marktzeiten/
  Countdown, Sommer-/Winterzeit über IANA-Zeitzonen), `scheduler`, `job_queue`
  (ein Discovery gleichzeitig, keine parallelen Vollanalysen, Duplikatschutz),
  `job_runner` (Fehlerisolation), `job_history`, `heartbeat`, `health`,
  `system_state`, `operations_cache`. Importiert nur `models`/`core`; die Jobs
  und die Uhr werden **injiziert** (kein Import aus der Pipeline, kein Zyklus).
- **Engine-Anbindung:** `engines/operations_engine.py` (Taktgeber `tick()`/
  `build_report()` + Regel-Laden), `operations_registry.py` (bekannte Job-Arten –
  einzige Erweiterungsstelle), `operations_cache.py` und `operations_result.py`
  (Re-Exporte).
- **Konfiguration:** `knowledge/operations_rules.toml` (Marktphasen je Markt,
  Zeitplan der Jobs, Heartbeat, Health, Historie); `core/paths.py`-Nähe über
  `OPERATIONS_RULES_FILE`. Alle Zeiten/Schwellen ausschließlich aus TOML.
- **Marktzeiten:** Europa (Vorbörse/Öffnung/Nachmittag/Schluss) und USA
  (Pre-Market/Opening-Bell/erste Handelsstunde/Nachmittag/Schluss); Sommer-/
  Winterzeit und Zeitzonen automatisch. **Market Clock** zeigt offene/geschlossene
  Börsen, die nächste Öffnung und Countdowns.
- **Dashboard:** neue Seite **Live Operations** (additiv über Router/Registry;
  `DashboardEngine` unverändert) mit Marktstatus, Systemstatus/Heartbeat/Queue,
  laufendem/nächstem Job, letztem Scan, Top Opportunities, neuen Chancen/Risiken
  und Job-Historie – visualisiert ausschließlich den OperationReport.
- **Tests:** 203 neue Tests (2040 gesamt).
- **Doku:** neue `docs/LIVE_OPERATIONS.md`; übrige Doku aktualisiert.

### Unverändert (bewusst)

- Keine neuen Strategien/Pattern/Scores/Risk-Regeln, keine Broker-API, keine
  automatische Orderausführung. Keine Änderung an einer bestehenden Engine oder
  an einem der bestehenden Frameworks (bis einschließlich Market Discovery) oder
  an der Dashboard-Engine. Parallelisierung und REST-API sind **vorbereitet**,
  aber bewusst noch nicht implementiert.

## [0.15.0] – 2026-07-12 – Sprint 15: Market Discovery Framework

Neues Framework, das AlphaAI **von Watchlists unabhängig** macht: das System
durchsucht den gesamten konfigurierten Markt selbstständig, filtert ungeeignete
Werte **vor** der vollständigen Analyse und priorisiert daraus die objektiv besten
Chancen. Der Benutzer gibt keine Aktien mehr vor. Die Discovery Engine
**berechnet niemals** Indikatoren, Muster, Strategien, Scores, Risiken oder
Empfehlungen – sie nutzt ausschließlich bereits vorhandene Ergebnisse (per
Injektion) und den **unveränderten** Market-Intelligence-Schritt.

### Hinzugefügt

- **Entities:** `models/market_discovery.py` (alle unveränderlich, `frozen`):
  `MarketDefinition`, `MarketSymbol`, `MarketUniverse`, `CandidateAnalysis`,
  `RejectedCandidate`, `DiscoveryOpportunity`, `DiscoveryStatistics`,
  `DiscoveryReport`.
- **Subsystem `market_discovery/`:** `universe_loader.py`, `market_universe.py`,
  `candidate_filter.py`, `candidate.py`, `sector_balancer.py`,
  `market_statistics.py`, `discovery_engine.py`, `discovery_cache.py`. Das
  Subsystem importiert ausschließlich `models`/`core`; die vorhandenen Ergebnisse
  je Wert und der Market-Intelligence-Schritt werden **injiziert**.
- **Engine-Anbindung:** `engines/market_discovery_engine.py`,
  `market_discovery_registry.py` (Registry der Märkte – einzige
  Erweiterungsstelle), `market_discovery_cache.py` und
  `market_discovery_result.py` (Re-Exporte).
- **Konfiguration:** `knowledge/market_discovery_rules.toml` (Universum,
  Vorfilter-Grenzwerte, Branchen-Ausgleich, Statistik, Anzeige); `core/paths.py`
  um `MARKET_DISCOVERY_RULES_FILE` ergänzt.
- **Märkte:** NYSE, NASDAQ, S&P 500, NASDAQ 100, Russell 2000, DAX, MDAX, SDAX,
  TecDAX, Euro Stoxx 50 (weitere problemlos ergänzbar).
- **Vorfilter:** Mindestkurs/-volumen/-liquidität/-historie, gültige Kurse,
  Handelbarkeit, keine Delistings, keine Penny Stocks (konfigurierbar); jeder
  verworfene Wert wird mit Grund festgehalten.
- **Branchen-Ausgleich:** konfigurierbar, keine festen Branchenlimits.
- **Dashboard:** neue Seite **Market Discovery** (additiv über Router/Registry;
  `DashboardEngine` unverändert) mit Top Opportunities, Gesamtmarkt-,
  Branchen- und Marktübersicht sowie Ranking (Suche/Filter) – visualisiert
  ausschließlich den DiscoveryReport.
- **Tests:** 145 neue Tests (1836 gesamt).
- **Doku:** neue `docs/MARKET_DISCOVERY.md`; übrige Doku aktualisiert.

### Unverändert (bewusst)

- Keine neuen Scores/Strategien/Pattern/Risk-Regeln, keine Broker-API, keine
  Echtgeldorders. Keine Änderung an einer bestehenden Engine, am Backtesting,
  Paper Trading, Analytics, am Market-Intelligence-Framework oder an der
  Dashboard-Engine.

## [0.14.0] – 2026-07-12 – Sprint 14: Market Intelligence Framework

Neues, **rein priorisierendes** Framework. Es **bewertet ausschließlich bereits
vorhandene Ergebnisse** (Empfehlung, Risiko, Analytics, Backtesting, Paper
Trading) und ordnet daraus die objektiv besten Chancen. Es **berechnet keine**
neue Handelsregel, verändert **keine** bestehenden Ergebnisse
(Recommendation/Risk/Score/Strategy/Pattern/Indicator/Analytics), trifft
**keine** Handelsentscheidung, hat **keinen** Broker und enthält **keine**
Machine-Learning-Komponenten.

### Hinzugefügt

- **Entities:** `models/opportunity.py` (alle unveränderlich, `frozen`):
  `MarketCandidate`, `OpportunityModelOutput`, `Opportunity`,
  `OpportunityStatistics`, `OpportunityExplanation`, `Watchlist`,
  `OpportunityReport`, `MarketIntelligenceContext`.
- **Subsystem `market_intelligence/`:** `base.py` (`BaseOpportunityModel`),
  `opportunity.py` (fünf Bewertungsmodelle + `build_opportunity`), `ranking.py`,
  `ranking_engine.py` (Ranking + Watchlists), `filter.py`, `explainer.py`,
  `statistics.py`, `cache.py` (`OpportunityCache`).
- **Engine-Anbindung:** `engines/market_intelligence_engine.py`,
  `market_intelligence_registry.py` (einzige Erweiterungsstelle – die Engine
  bleibt für neue Modelle unverändert), `market_intelligence_cache.py` und
  `market_intelligence_result.py` (Re-Exporte).
- **Konfiguration:** `knowledge/market_intelligence_rules.toml` (Gewichte +
  Ranking-/Watchlist-/Statistik-Parameter, Gewichte ergeben 1.0); `core/paths.py`
  um `MARKET_INTELLIGENCE_RULES_FILE` ergänzt; neue Fehlerklasse
  `MarketIntelligenceParameterError`.
- **Opportunity Score:** gewichtete Zusammenfassung von Recommendation, Risk,
  Analytics, Backtesting und Paper Trading – **kein neues Bewertungssystem**.
  Fehlt eine Quelle, wird über die verbleibenden Gewichte normalisiert.
- **Ranking/Filter/Sortierung/Explainer/Statistik/Watchlists** wie spezifiziert
  (Top 5/10/20/50; Long/Short/Watch; transparente Herleitung „warum Platz N").
- **Dashboard:** neue Seite **Market Intelligence** (additiv über Router/Registry;
  `DashboardEngine` unverändert) mit Top Opportunities, Ranking (Suche/Filter),
  Heatmap, Erklärung und Kennzahlen – visualisiert ausschließlich den
  `OpportunityReport`, **keine** Berechnung im Frontend.
- **Tests:** 201 neue Tests (1690 gesamt).
- **Doku:** neue `docs/MARKET_INTELLIGENCE.md`; übrige Doku aktualisiert.

### Unverändert (bewusst)

- Keine neue Handelsregel, keine Broker-API, keine Echtgeldorders, keine ML. Keine
  Änderung an einer bestehenden Engine, am Backtesting, Paper Trading, Analytics
  oder an der Dashboard-Engine.

## [0.13.0] – 2026-07-11 – Sprint 13: AlphaAI Command Center

Neues, **rein darstellendes** Dashboard („AlphaAI Command Center"). Es ist
**ausschließlich** die Presentation Layer: es **berechnet niemals** Daten,
enthält **keinerlei** Geschäftslogik und erzeugt **keine** Scores, Risiken,
Empfehlungen, Analysen, Kennzahlen oder Statistiken. Alle angezeigten Werte
stammen **einzig** aus den bereits vorhandenen Reports (`AnalyticsReport`,
`PaperTradingReport`, `BacktestReport`, `RecommendationReport`, `RiskReport`,
`ScoreReport`, `StrategyReport`, `PatternReport`, `IndicatorResult`). Fehlt ein
Wert, wird er lediglich als Platzhalter angezeigt – **keine** Ersatzberechnung.
Keine Änderung an einer bestehenden Engine, am Backtesting, am Paper Trading
oder am Analytics-Framework.

### Hinzugefügt

- **Entities:** `models/dashboard.py` (alle unveränderlich, `frozen`):
  `MetricCard`, `StatusItem`, `ChartSeries`, `ChartSpec`, `TableSpec`,
  `WidgetSpec`, `DashboardView` (reine Anzeige-Beschreibungen, keine Logik).
- **Paket `dashboard/`:** `theme.py` (die **einzige** Quelle des Aussehens –
  Dark-Carbon-Palette, Typografie, Abstände, Rahmen, Animationen, Icons,
  Materialien, Chart-Palette; keine Hardcodes im übrigen Code), `state.py`
  (`DashboardState` mit Snapshot/Restore – der Zustand geht nie verloren),
  `format.py` (reine Anzeige-Formatierung), `charts.py` (Chart-Specs),
  `status.py` (Modul-Status aus Vorhandensein), `settings.py` +
  `settings.toml` (nur Anzeigeoptionen – **keine** Handelsparameter),
  `viewmodels.py` (lesen Reports ab, berechnen nichts), `responsive.py`
  (Desktop/Tablet/UltraWide/4K), `feedback.py` (Lade-/Fehlerzustände – keine
  Exceptions im Frontend).
- **Widget-System:** `dashboard/widgets/` mit 26 unabhängigen Widgets (jedes
  liest nur das View Model und formatiert), `widget_registry.py` (die
  **einzige** Stelle zum Registrieren neuer Widgets), `router.py` (9 Seiten:
  Overview, Live Analysis, Paper Portfolio, Backtesting, Analytics,
  Performance, Trade Journal, Recommendations, Settings; Tastenkürzel), sowie
  `engine.py` (`DashboardEngine` – setzt Ansichten zusammen und bleibt für
  neue Widgets/Seiten **unverändert**, Open/Closed).
- **Streamlit-Schicht:** `render.py` und `app.py` sind die **einzigen** Stellen
  mit Streamlit-Import (lazy, `# pragma: no cover`); die gesamte übrige Logik
  ist Streamlit-frei und vollständig testbar.
- **Tests:** 259 neue Tests (1488 gesamt) – Modelle, Theme, State, Format,
  Charts, Status, Settings, View Models, alle Widgets, Registry, Router,
  Responsive, Feedback und die Engine (inkl. Lade-/Fehler-/Isolationsfälle).
- **Doku:** neue `docs/DASHBOARD.md`; übrige Doku aktualisiert.

### Unverändert (bewusst)

- Keine Berechnung, keine Geschäftslogik, keine Broker-API, keine
  Handelsparameter, keine ML-Komponenten. Auto-Refresh lädt ausschließlich neue
  Reports und startet **niemals** eine Berechnung. Kein Smartphone-Ziel.

## [0.12.0] – 2026-07-11 – Sprint 12: Trading Intelligence & Analytics Framework

Neues, **rein auswertendes** Analytics-Framework. Es analysiert **ausschließlich**
bereits vorhandene Daten aus Backtesting und Paper Trading und erzeugt daraus
**objektive, reproduzierbare Statistiken**. Es **bewertet keine** Trades, trifft
**keine** Handelsentscheidung, verändert **keine** bestehenden Ergebnisse,
erzeugt **keine** neuen Empfehlungen und enthält **keine**
Machine-Learning-Komponenten. Keine Änderung an einer bestehenden Engine, am
Backtesting oder am Paper Trading.

### Hinzugefügt

- **Entities:** `models/analytics.py` (alle unveränderlich, `frozen`):
  `AnalyticsTrade`, `GroupStatistics`, `AnalyticsModelOutput`,
  `AnalyticsContext`, `AnalyticsResult`, `AnalyticsReport`.
- **Subsystem `analytics/`:** `aggregation.py` (reine Kennzahl-Bausteine),
  `labeling.py` (Ableitung Strategie/Risiko-Level/Score aus
  `recommendation_id`/`reasons`), `normalization.py` (Backtest-/Paper-Trades →
  `AnalyticsTrade`), zehn unabhängige Analysemodelle (`trade_statistics`,
  `performance_analyzer`, `pattern_analysis`, `strategy_analysis`,
  `recommendation_analysis`, `risk_analysis`, `market_analysis`, `time_analysis`,
  `journal_analysis`, `summary_analysis`) und `base.py` (`BaseAnalyticsModel`).
- **Engine-Anbindung:** `engines/analytics_engine.py`, `analytics_registry.py`
  (einzige Erweiterungsstelle – die Engine bleibt für neue Modelle unverändert),
  `analytics_cache.py` (FIFO), `analytics_result.py` (Re-Export).
- **Konfiguration:** `knowledge/analytics_rules.toml`; `core/paths.py` um
  `ANALYTICS_RULES_FILE` ergänzt; neue Fehlerklasse `AnalyticsParameterError`.
- **AnalyticsResult** enthält u. a.: Analytics-ID, Backtest-ID, PaperTrading-ID,
  Trade Count, Win/Loss Rate, Profit Factor, Expectancy, Average Winner/Loser,
  Maximum Drawdown, Average Holding Time, Average Risk Reward, Long/Short/
  Strategy/Pattern/Recommendation/Risk/Market/Time/Journal Statistics,
  Performance, Summary, Warnings, Metadata, Timestamp.
- **Analysen:** LONG/SHORT, Recommendation Strength, Risiko-Level, Strategie,
  Score, Pattern/Marktphase/Volatilität/Liquidität (label-basiert, erweiterbar)
  sowie Zeit (Wochentag/Monat/Handelsstunde/Haltedauer).
- **Validierung:** leere Reports, fehlende Trades, nicht registrierte Modelle,
  ungültige Parameter/Kennzahlen.
- **Tests:** 184 neue Tests (1229 gesamt) – Engine, Registry, Cache, Aggregation,
  Labeling, Normalisierung, alle zehn Analysen und echte End-to-End-Szenarien.
- **Doku:** neue `docs/ANALYTICS.md`; übrige Doku aktualisiert.

### Unverändert (bewusst)

- Keine Dashboard-Komponenten, keine Broker-API, keine Handelslogik, keine neuen
  Empfehlungen, keine ML-Komponenten. Alle Kennzahlen liegen fertig berechnet im
  `AnalyticsResult` vor (Vorbereitung für ein rein visualisierendes Dashboard).

## [0.11.0] – 2026-07-10 – Sprint 11: Paper Trading Framework

Neues, **rein bewertendes** Paper-Trading-Framework. Es nutzt ausschließlich die
**bestehende** Pipeline, erzeugt **keine** neue Handelsregel, ändert **keine**
Engine und **kein** Backtesting, führt **niemals** echte Orders aus (Trades
werden ausschließlich simuliert) und hat **keine** Broker-API.

### Hinzugefügt

- **Entities:** `models/paper_trading.py` (alle unveränderlich, `frozen`):
  `PaperOrder`, `PaperPosition`, `PaperTrade`, `JournalEntry`, `PaperEquityPoint`,
  `PaperStatistics`, `PaperPerformance`, `PaperTradingContext`/`ModelOutput`,
  `PaperTradingResult`, `PaperTradingReport` samt Enums `OrderAction`,
  `PositionStatus`, `CloseReason`.
- **Subsystem `paper_trading/`:** `paper_runner.py` (tägliche Simulation über die
  bestehende Pipeline, **kein** Look-Ahead), `portfolio.py` (simuliertes
  Portfolio mit Validierung), `position.py` (Mark-to-Market, Stop/Take-Profit,
  Trailing Stop **vorbereitet**), `order.py` (Statuswechsel), `trade.py`,
  `journal.py`, `statistics.py`, `performance.py`, `base.py`
  (`BasePaperTradingModel`) sowie `statistics_model`/`performance_model`.
- **Engine-Anbindung:** `engines/paper_trading_engine.py`,
  `paper_trading_registry.py` (einzige Erweiterungsstelle),
  `paper_trading_cache.py` (FIFO), `paper_trading_result.py` (Re-Export).
- **Konfiguration:** `knowledge/paper_trading_rules.toml`; `core/paths.py` um
  `PAPER_TRADING_RULES_FILE` ergänzt; neue Fehlerklassen
  `PaperTradingParameterError` und `PaperTradingValidationError`.
- **PaperTradingResult** enthält u. a.: Paper-Trading-ID, Recommendation-ID,
  Direction, Recommendation Strength, Entry/Current/Exit Price, Position Size,
  (Fractional) Shares, Status (OPEN/CLOSED/CANCELLED), Entry/Exit Time, PnL €/%,
  Running/Maximum Drawdown, Current Equity, Portfolio Exposure, Reasons,
  Warnings, Metadata, Timestamp.
- **Order-Management** (OPEN/CLOSE/CANCEL/EXPIRE), **Journal** (automatische
  Dokumentation je Eröffnung/Schließung), **Statistik** (Win/Loss Rate, Profit
  Factor, Ø Winner/Loser, Ø Haltedauer, Kapital, Rendite, offene/geschlossene
  Positionen).
- **Validierung:** keine doppelte Position derselben Empfehlung, keine negative
  Positionsgröße, keine ungültigen Preise/Zeitstempel, keine ungültigen
  Statuswechsel.
- **Tests:** 177 neue Tests (1045 gesamt) – Engine, Portfolio, Journal, Order-/
  Position-Management, Registry, Cache, Performance, Statistik, Regeln,
  Domänenmodelle und echte Szenarien (durch die reale Pipeline).
- **Doku:** neue `docs/PAPER_TRADING.md`; übrige Doku aktualisiert.

### Unverändert (bewusst)

- Keine Dashboard-Logik, keine Broker-API, keine echten Orders, keine
  automatische Orderausführung, keine neue Handelsregel, keine Änderung an der
  bestehenden Analysepipeline. `settings.toml` bleibt die einzige Quelle der
  Konto-/Risikoeinstellungen.

## [0.10.0] – 2026-07-10 – Sprint 10: Historical Backtesting Framework

Neues, **rein bewertendes** Backtesting-Framework. Es nutzt ausschließlich die
**bestehende** Pipeline, erzeugt **keine** neue Handelsregel, ändert **keine**
Empfehlung und **keine** Engine (Indicator/Pattern/Strategy/Score/Risk/
Recommendation bleiben unverändert). Es werden **keine** echten Orders
ausgeführt; Trades werden ausschließlich rechnerisch simuliert.

### Hinzugefügt

- **Entities:** `models/backtest.py` (alle unveränderlich, `frozen`):
  `HistoricalSignal`, `SimulatedTrade` (mit `TradeOutcome`/`ExitReason`),
  `EquityPoint`, `BenchmarkResult`, `BacktestModelOutput`, `BacktestContext`,
  `BacktestResult`, `BacktestReport`.
- **Subsystem `backtesting/`:** `historical_runner.py` (führt die Pipeline
  fensterweise über die Historie aus – **kein** Look-Ahead), `trade_simulator.py`
  (simuliert Trades mit Entry/Exit/Stop/Take-Profit, Fractional Shares, Kosten),
  `performance_metrics.py`, `equity_curve.py`, `statistics.py` (Sharpe/Sortino/
  Calmar – **vorbereitet**), `benchmark.py` (Buy & Hold), `base.py`
  (`BaseBacktestModel`) sowie vier Modelle (`performance_model`,
  `drawdown_model`, `ratio_model`, `benchmark_model`).
- **Engine-Anbindung:** `engines/backtest_engine.py`, `backtest_registry.py`
  (einzige Erweiterungsstelle), `backtest_cache.py` (FIFO), `backtest_result.py`
  (Re-Export).
- **Konfiguration:** `knowledge/backtest_rules.toml` (Historical-Runner-,
  Simulations- und Modellparameter); `core/paths.py` um `BACKTEST_RULES_FILE`
  ergänzt; neue Fehlerklasse `BacktestParameterError`.
- **BacktestResult** enthält u. a.: Backtest-ID, Symbol, Timeframe, Start-/End-
  datum, Anzahl Signale/Trades, Win/Loss Rate, Profit Factor, Ø Gewinn/Verlust,
  Ø CRV, Ø Haltedauer, Max Drawdown, Expectancy, Sharpe/Sortino/Calmar
  (vorbereitet), Equity Curve, Trade-Liste, Benchmark, Summary, Metadata,
  Timestamp. Jeder Trade ist vollständig nachvollziehbar (Entry/Exit/Stop/
  Take-Profit/Risk/Recommendation/Direction/Strength/Reasons/Warnings).
- **Validierung:** ungültige Zeiträume, fehlende Daten, leere Historie,
  ungültige Preise, ungültige Trades/Kennzahlen.
- **Benchmark:** optionaler Vergleich gegen Buy & Hold (Referenz, keine
  Empfehlung).
- **Tests:** 155 neue Tests (868 gesamt) – Engine, Registry, Cache, Trade-
  Simulator, Performance Metrics, Statistik, Benchmark, Regeln, Domänenmodelle
  und echte historische Szenarien (durch die reale Pipeline).
- **Doku:** neue `docs/BACKTESTING.md`; übrige Doku aktualisiert.

### Unverändert (bewusst)

- Keine Dashboard-Logik, keine Broker-API, keine automatische Orderausführung,
  keine Paper-Trading-Funktionen, keine neue Handelsregel. `settings.toml` bleibt
  die einzige Quelle der Konto-/Risikoeinstellungen.

## [0.9.6] – 2026-07-09 – Sprint 9.6: Recommendation Semantics

Reiner Semantik-/Domänenmodell-Sprint. **Keine** neuen Features, **keine** neue
Engine, **keine** geänderten Handelsregeln, **keine** neue Bewertungslogik. Der
in 9.5 dokumentierte Befund *„Strong bearish setup → STRONG_BUY"* ist behoben.

### Geändert (Semantik)

- **Richtung und Qualität vollständig getrennt** in `RecommendationResult`:
  - neu `direction: Direction` (LONG/SHORT/NEUTRAL) – ausschließlich die
    Handelsrichtung, abgeleitet aus der Strategie-Hypothese.
  - `recommendation_level` → `recommendation_strength: RecommendationStrength`
    (VERY_HIGH/HIGH/MEDIUM/LOW/REJECT) – ausschließlich die Qualität; enthält
    **kein** BUY/SELL/LONG/SHORT mehr.
- **Mappings/Benennung** angepasst (Werte unverändert): `strength_from_rating`,
  `cap_strength`, `action_for_strength`, `strength_severity`; Schwellen in
  `recommendation_rules.toml` (`very_high_min`/`high_min`/`medium_min`/`low_min`)
  und Gate-Parameter (`max_overall_risk_for_high`, `min_consensus_for_high`).
- **Validierung** ergänzt: Richtung und Stärke werden geprüft; die Stärke kann
  strukturell nie eine Richtung darstellen (`RecommendationReport.by_strength`/
  `by_direction`).
- **Zusammenfassung** nennt Richtung und Stärke getrennt (z. B.
  „SHORT / VERY_HIGH — …").
- Die **Bewertungslogik ist unverändert**: Rating-Werte sind identisch zu 9.5
  (`trend_up` → LONG/VERY_HIGH, `trend_down` → SHORT/VERY_HIGH, `sideways` →
  MEDIUM).

### Tests

- Alle Recommendation-/Integrationstests auf `direction`/`strength` umgestellt;
  neue Tests für LONG/SHORT/NEUTRAL und die Garantie, dass ein bärisches Setup
  nie als „BUY" erscheint. Gesamt 713 (unverändert grün).

### Qualitätsprüfung

Import-Zyklen: 0. Plugin-Unabhängigkeit/SOLID: 0. Immutability vollständig.
`ruff`/`black` konform. 713 Tests grün. `VALIDATION_REPORT.md` aktualisiert
(Befund behoben).

### ADR

ADR-030 (Trennung von Direction und RecommendationStrength).

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
