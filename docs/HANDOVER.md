# Handover (Übergabe)

_Diese Datei wird nach jedem Sprint automatisch aktualisiert._ Sie ermöglicht
es einer neuen Sitzung (Mensch oder KI), nahtlos weiterzuarbeiten – **ohne**
dass Wissen nur im Chat existiert.

## Stand der Übergabe

- **Datum:** 2026-07-12
- **Abgeschlossener Sprint:** Sprint 17 – Production Backend & Mobile API Platform
  (endgültiges Backend; Sprint 18 = ausschließlich Android-App, keine
  Engine-Änderungen nötig)
- **Projektwurzel:** `AlphaAI/` (im Repository `AlphaAI` ist dies die Wurzel)
- **Branch:** `claude/alphaai-project-bootstrap-c51pse`
- **Tag:** `v0.1.0-foundation` (stabiler Fundament-Stand nach Sprint 7.5)

## So startet die nächste Sitzung

1. In das Projektverzeichnis wechseln: `cd AlphaAI`.
2. Umgebung einrichten: `python3.12 -m venv .venv && source .venv/bin/activate`.
3. Installieren: `pip install -e ".[dev]"`.
4. Fundament prüfen: `python -m scripts.check_setup`.
5. Tests ausführen: `pytest` (aktuell 2294 Tests).
6. Architektur prüfen: `python scripts/quality_check.py` (muss BESTANDEN melden).

> **Semantik (ab 9.6):** `RecommendationResult.direction` (LONG/SHORT/NEUTRAL)
> und `RecommendationResult.recommendation_strength`
> (VERY_HIGH/HIGH/MEDIUM/LOW/REJECT) sind getrennt. Die Stärke enthält **kein**
> BUY/SELL/LONG/SHORT. Ein bärisches Setup ist SHORT mit ggf. hoher Stärke.

## Backend-Betrieb (ab Sprint 17)

- AlphaAI läuft als **produktiver Backend-Dienst**. Composition Root:
  `engines/application_engine.py` (`ApplicationEngine.from_config(...)`).
- Persistenz: SQLite (`database/alpha_ai_reports.db`), neustartfest; immer der
  letzte erfolgreiche Scan. Parameter in `knowledge/application_rules.toml`.
- REST-API (`/api/v1`, JSON): framework-unabhängiger Kern
  (`application/api/`) + optionaler FastAPI-Adapter (`engine.create_fastapi_app()`).
  Zugriff vorerst nur lokal.
- Grundsatz: API/Backend **liefern** nur vorhandene Reports – keine Berechnung,
  keine Order, keine Handelsentscheidung. Details: `docs/API.md`,
  `docs/BACKEND.md`, `docs/PRODUCTION.md`.

## Qualitätsprüfung Sprint 17 (Ergebnis)

Vor dem Commit automatisch geprüft:

| Prüfung | Ergebnis |
|---|---|
| Import-Zyklen | **0** |
| Entities-Schicht `models/` (kein Import aus höheren Schichten) | **0 Verstöße** |
| Plugin-Unabhängigkeit | **0 Verstöße** |
| SOLID-Heuristik | **0 Verstöße** |
| Pipeline-Konsistenz (`verify_pipeline`) | **0 Verstöße** |
| Ergebnisobjekte unveränderlich (`frozen`) | **vollständig** |
| Ruff / Black | **konform** |
| pytest | **2040 bestanden** |

## Vollständige Pipeline – Einstieg

```python
from pipeline.runner import IntegrationRunner
runner = IntegrationRunner.from_config()
result = runner.run(market_result, symbol="AAPL")   # oder runner.run_frame(ohlcv_df, "AAPL")
best = result.best()                                 # höchstbewertete Empfehlung (nur Anzeige)
```

`pipeline.consistency.verify_pipeline(result)` prüft die Referenz-Konsistenz
(leer = ok). Datenfluss: `docs/PIPELINE.md`. Validierungsergebnisse und offene
Kalibrierungspunkte: `docs/VALIDATION_REPORT.md`.

**Nächster fachlicher Schritt (aus dem Validation Report):** Schwellen/Gewichte
der Empfehlung an realen historischen Daten kalibrieren und die vorbereiteten
Backtest-Kennzahlen (Sharpe/Sortino/Calmar) annualisieren/kalibrieren. Das sind
eigene Sprints und ändern bewusst Verhalten.

## Backtesting-Framework – Kurzüberblick für die Weiterarbeit

- Einstieg: `BacktestEngine.from_config()` lädt `knowledge/backtest_rules.toml`
  und `config/settings.toml`, baut den bestehenden `IntegrationRunner` und
  registriert alle Standard-Backtest-Modelle.
- Backtest: `engine.run_frame(ohlcv_df, symbol=...)` → `BacktestResult` bzw.
  `engine.run(market_result)` → `BacktestReport` (eines je Symbol).
- **Rein bewertend:** nutzt ausschließlich die bestehende Pipeline, erzeugt
  **keine** neue Handelsregel, ändert **keine** Empfehlung, führt **keine** echte
  Order aus (nur Simulation). Kein Look-Ahead (fensterweise `frame.iloc[:i+1]`).
  Fractional Shares; Konto-/Risikowerte ausschließlich aus `settings.toml`.
- Jeder `SimulatedTrade` ist vollständig nachvollziehbar (Entry/Exit/Stop/
  Take-Profit/Risk/Recommendation/Direction/Strength/Reasons/Warnings).
- **Neues Backtest-Modell hinzufügen** (einziger erlaubter Weg):
  1. Datei in `backtesting/` anlegen, `BaseBacktestModel` implementieren
     (`compute`), nur `context`/`params` nutzen.
  2. In `engines/backtest_registry.py::build_default_registry` registrieren.
  3. Abschnitt/Parameter in `knowledge/backtest_rules.toml` ergänzen. Die Engine
     muss dafür **nicht** geändert werden.
  4. Eigene Testdatei `tests/test_backtest_<name>.py` anlegen.
- Details/Datenfluss: `docs/BACKTESTING.md`.

## Paper-Trading-Framework – Kurzüberblick für die Weiterarbeit

- Einstieg: `PaperTradingEngine.from_config()` lädt
  `knowledge/paper_trading_rules.toml` und `config/settings.toml`, baut den
  bestehenden `IntegrationRunner` und registriert alle Standard-Modelle.
- Simulation: `engine.run_frame(ohlcv_df, symbol=...)` → `PaperTradingReport`
  bzw. `engine.run(market_result)` → `PaperTradingReport` (ein gemeinsames Depot).
- **Rein bewertend:** tägliche Simulation über die bestehende Pipeline,
  **niemals** echte Orders, **keine** Broker-API, **keine** neue Handelsregel.
  Kein Look-Ahead. Fractional Shares; Konto-/Risikowerte ausschließlich aus
  `settings.toml`.
- Jede `PaperPosition`/jedes `PaperTradingResult` ist vollständig nachvollziehbar
  (Recommendation-ID/Direction/Strength/Reasons/Warnings). Order-Management
  (OPEN/CLOSE/CANCEL/EXPIRE), automatisches Journal, Statistik/Performance.
- **Portfolio/Journal sind Manager** (mutabel); **Ergebnis-/Snapshot-Typen sind
  `frozen`** – Positionen werden über `dataclasses.replace` fortgeschrieben.
- **Neues Paper-Trading-Modell hinzufügen** (einziger erlaubter Weg):
  1. Datei in `paper_trading/` anlegen, `BasePaperTradingModel` implementieren
     (`compute`), nur `context`/`params` nutzen.
  2. In `engines/paper_trading_registry.py::build_default_registry` registrieren.
  3. Abschnitt/Parameter in `knowledge/paper_trading_rules.toml` ergänzen. Die
     Engine muss dafür **nicht** geändert werden.
  4. Eigene Testdatei `tests/test_paper_<name>.py` anlegen.
- **Vorbereitet:** Trailing Stop (`position.apply_trailing_stop`, inaktiv per
  `trailing_distance = 0.0`). Details/Datenfluss: `docs/PAPER_TRADING.md`.

## Analytics-Framework – Kurzüberblick für die Weiterarbeit

- Einstieg: `AnalyticsEngine.from_config()` lädt `knowledge/analytics_rules.toml`
  und registriert alle zehn Standard-Analysemodelle.
- Auswertung: `engine.analyze(backtest_report, paper_report, symbol=...)` →
  `AnalyticsReport` (`.result` ist das `AnalyticsResult` mit allen Kennzahlen).
  Eine Quelle genügt (`analyze(backtest_report)` oder
  `analyze(paper_report=paper_report)`).
- **Rein auswertend:** liest ausschließlich bestehende Reports, **bewertet keine**
  Trades, verändert **nichts**, erzeugt **keine** Empfehlung, **kein** ML.
  Dimensionen (Strategie/Risiko/Score) werden reproduzierbar aus
  `recommendation_id`/`reasons` abgeleitet; fehlende Angaben ⇒ ``"unbekannt"``.
- **Ergebnistypen sind `frozen`**; alle Kennzahlen liegen fertig im
  `AnalyticsResult` (dashboard-fertig – ein Dashboard darf nur visualisieren).
- **Neues Analysemodell hinzufügen** (einziger erlaubter Weg):
  1. Datei in `analytics/` anlegen, `BaseAnalyticsModel` implementieren
     (`compute`), nur `context`/`params` nutzen – unabhängig von anderen Modellen.
  2. In `engines/analytics_registry.py::build_default_registry` registrieren. Die
     **Engine bleibt unverändert** (Open/Closed).
  3. Abschnitt/Parameter in `knowledge/analytics_rules.toml` ergänzen.
  4. Eigene Testdatei `tests/test_analytics_<name>.py` anlegen.
- Pattern-/Markt-Labels sind erweiterbar über die Trade-Metadata (ohne
  Engine-Änderung). Details/Datenfluss: `docs/ANALYTICS.md`.

## Dashboard / Command Center – Kurzüberblick für die Weiterarbeit

- Einstieg: `DashboardEngine.from_config()` lädt `dashboard/settings.toml`
  (nur Anzeigeoptionen), das Standard-Theme und alle 26 Standard-Widgets.
- Ansicht: `engine.build_view(state, bundle)` → `DashboardView`. `state` ist ein
  `DashboardState` (Seite/Filter/…), `bundle` ein `ReportBundle` der bestehenden
  Reports. Rendern nur über `dashboard/render.py` bzw. Start über
  `streamlit run dashboard/app.py`.
- **Rein darstellend:** liest ausschließlich Reports, **berechnet nichts**,
  enthält **keine** Geschäftslogik, erzeugt **keine** Kennzahlen. Fehlt ein Wert,
  wird nur ein Platzhalter (`—`) angezeigt. Auto-Refresh lädt **nur** Reports.
- **Neues Widget hinzufügen** (einziger erlaubter Weg):
  1. Klasse von `BaseWidget` ableiten (`build(context)` → `WidgetSpec`), nur das
     View Model lesen, kein anderes Widget importieren.
  2. In `dashboard/widget_registry.py::_DEFAULT_WIDGETS` registrieren. Die
     **Engine bleibt unverändert** (Open/Closed).
  3. Im `dashboard/router.py` einer Seite/Region zuordnen.
  4. Eigene Testdatei/Testfälle in `tests/test_dashboard_widgets.py` ergänzen.
- **Neue Seite** nur über `dashboard/router.py`; **Aussehen** nur über
  `dashboard/theme.py`. Details/Datenfluss: `docs/DASHBOARD.md`.

## Market Intelligence – Kurzüberblick für die Weiterarbeit

- Einstieg: `MarketIntelligenceEngine.from_config()` lädt
  `knowledge/market_intelligence_rules.toml` und registriert die fünf
  Bewertungsmodelle.
- Priorisierung: `engine.analyze(candidates)` → `OpportunityReport`. Jeder
  `MarketCandidate` bündelt je Aktie Ticker/Metadaten plus die bereits
  vorhandenen Reports (Recommendation/Analytics/Backtest/Paper Trading, alle
  optional). Ergebnis: `report.opportunities` (Rang 1 zuerst), `report.statistics`,
  `report.explanations`, `report.watchlists`.
- **Rein priorisierend:** bewertet ausschließlich vorhandene Ergebnisse, erzeugt
  **keine** neue Handelsregel, verändert **nichts**. Der Opportunity Score ist die
  gewichtete Zusammenfassung (Recommendation/Risk/Analytics/Backtest/Paper Trading);
  fehlt eine Quelle, wird über die verbleibenden Gewichte normalisiert. Eine Aktie
  ohne Empfehlung ist „Watch" (Score 0).
- **Neues Bewertungsmodell hinzufügen** (einziger erlaubter Weg):
  1. Datei/Klasse `BaseOpportunityModel` in `market_intelligence/opportunity.py`
     umsetzen (`compute`), nur `context`/`params` nutzen.
  2. In `engines/market_intelligence_registry.py::build_default_registry`
     registrieren. Die **Engine bleibt unverändert** (Open/Closed).
  3. Abschnitt mit `weight` in `knowledge/market_intelligence_rules.toml` ergänzen
     (die Summe der aktivierten Gewichte muss 1.0 bleiben).
- Ranking/Filter/Sortierung/Explainer/Statistik liegen in eigenen Modulen; die
  Dashboard-Seite „Market Intelligence" visualisiert nur den Report. Details:
  `docs/MARKET_INTELLIGENCE.md`.

## Market Discovery – Kurzüberblick für die Weiterarbeit

- Einstieg: `MarketDiscoveryEngine.from_config()` lädt
  `knowledge/market_discovery_rules.toml`, die Markt-Registry (10 Märkte) und den
  bestehenden Market-Intelligence-Schritt.
- Durchsuchen: `engine.discover(markets=None, symbol_source=…, analysis_provider=…)`
  → `DiscoveryReport`. `markets` ist optional (Standard: `default_markets`).
  **`symbol_source`** liefert je Markt die Werte (Stammdaten), **`analysis_provider`**
  je Wert die **bereits vorhandenen** Ergebnisse (Recommendation/Analytics/Backtest/
  Paper) aus der bestehenden Pipeline. Beide werden **injiziert** – die Engine
  berechnet nichts selbst und importiert nichts aus der Pipeline.
- Ablauf: Universum laden → Vorfilter (`candidate_filter`) → Kandidaten
  (`candidate`) → Market Intelligence (unverändert) → Branchen-Ausgleich
  (`sector_balancer`) → Statistik → Report. Verworfene Werte stehen mit Grund in
  `report.rejected`.
- **Neuer Markt:** `MarketDefinition` in
  `engines/market_discovery_registry.py::_DEFAULT_MARKETS` ergänzen – die Engine
  bleibt unverändert. **Grenzwerte/Ausgleich:** nur über die Regeldatei. Details:
  `docs/MARKET_DISCOVERY.md`.

## Live Operations – Kurzüberblick für die Weiterarbeit

- Einstieg: `OperationsEngine.from_config(jobs=…)` lädt
  `knowledge/operations_rules.toml` (Marktphasen, Zeitplan, Heartbeat/Health) und
  die Job-Registry. Die eigentlichen Jobs werden als `jobs={job_type: callable}`
  **injiziert** (z. B. `{"discovery": lambda: discovery_engine.discover(...)}`);
  die Uhr über `clock=` (UTC). Die Engine importiert **nichts** aus der Pipeline.
- Betrieb: periodisch `engine.tick()` aufrufen (z. B. jede Minute); es setzt den
  Heartbeat, startet fällige Jobs (seriell, ein Discovery gleichzeitig, Fehler
  isoliert) und liefert einen `OperationReport`. `engine.build_report()` liefert
  den Report ohne Jobs zu starten (für reine Anzeige).
- Der `OperationReport` ist **UI-unabhängig**: Marktstatus/Countdown,
  laufender/nächster Job, letzter Scan, Systemzustand (Health/Heartbeat/Queue),
  Zähler/Laufzeiten, letzter Discovery-Report (Top Opportunities) sowie neue
  Chancen/Risiken. Dashboard/REST/Mobile nutzen denselben Report.
- **Niemals Orders**; das System orchestriert nur. **Neue Job-Art:**
  `JobDefinition` in `engines/operations_registry.py` ergänzen, im Zeitplan
  verwenden und die Funktion injizieren – die Engine bleibt unverändert.
  **Marktzeiten/Zeitplan:** nur über die Regeldatei. Details:
  `docs/LIVE_OPERATIONS.md`.

## Recommendation Engine – Kurzüberblick für die Weiterarbeit

- Einstieg: `RecommendationEngine.from_config()` lädt
  `knowledge/recommendation_rules.toml` und registriert alle Standard-Modelle.
- Empfehlung: `engine.recommend(strategy_report, score_report, risk_report,
  symbol=...)` → `RecommendationReport` mit einer `RecommendationResult` je
  bewerteter Hypothese (zugeordnet über `hypothesis_id`).
- Ergebnis: `report.results`; `report.top(n)`/`by_level`/`by_action` sind reine
  Anzeige. Jede `RecommendationResult` trägt Level, Handlung, Confidence (0-1),
  Overall Rating (0-100), Reasons, Warnings, Summary und in `metadata['factors']`
  die sechs Faktoren.
- **Neues Recommendation-Modell hinzufügen** (einziger erlaubter Weg):
  1. Datei in `recommendation/` anlegen, `BaseRecommendationModel` implementieren
     (`compute`), nur `context`/`params` nutzen, kein anderes Modell importieren.
  2. In `engines/recommendation_registry.py::build_default_registry` registrieren.
  3. Abschnitt/Parameter in `knowledge/recommendation_rules.toml` ergänzen. Die
     Engine muss dafür **nicht** geändert werden.
  4. Eigene Testdatei `tests/test_recommendation_<name>.py` anlegen.
- **Grundsatz:** No-Trade ist vollwertig; ein hoher Score allein führt nie zu
  BUY. Die Engine erzeugt **keine** Order und **keine** Broker-Anbindung.

## Risk Engine – Kurzüberblick für die Weiterarbeit

- Einstieg: `RiskEngine.from_config()` lädt `knowledge/risk_rules.toml` und
  `config/settings.toml` und registriert alle Standard-Modelle.
- Bewertung: `engine.assess(score_report, indicators, data=frame, symbol=...,
  open_positions=(...))` → `RiskReport` mit einem `RiskResult` je Score.
- Ergebnis: `report.results`; `report.highest_risk(n)` sortiert nach Risiko
  (reine Anzeige, **keine** Empfehlung). Jeder `RiskResult` trägt die zehn
  Komponenten in `risk_components`, alle Modellwerte in
  `metadata['model_values']` und erklärbare Beitragszeilen in `reasons`.
- **Neues Risk-Modell hinzufügen** (einziger erlaubter Weg):
  1. Datei in `risk/` anlegen, `BaseRiskModel` implementieren (`compute`),
     `component` auf einen Namen aus `RISK_COMPONENT_NAMES` setzen (oder `""`),
     nur `context`/`params` nutzen, kein anderes Modell importieren.
  2. In `engines/risk_registry.py::build_default_registry` registrieren.
  3. Abschnitt + ggf. Gewicht in `knowledge/risk_rules.toml` ergänzen. Die
     Engine muss dafür **nicht** geändert werden.
  4. Eigene Testdatei `tests/test_risk_<name>.py` anlegen.
- **Konto-/Depotwerte** kommen ausschließlich aus `settings.toml`, alle übrigen
  Parameter aus `risk_rules.toml`. Die Engine erzeugt **keine** Order.

## Architektur-Konsolidierung (Sprint 7.5) – für die Weiterarbeit

- **Datentypen** liegen in `models/` (`market`, `indicator`, `pattern`,
  `strategy`, `score`; `risk`/`recommendation` vorbereitet). Neue Datentypen
  dort anlegen. Alte Pfade (`data.market_result`, `engines.*_result`,
  `*/base.py`) re-exportieren weiterhin – bestehender Code bleibt gültig.
- **Ergebnisobjekte sind `frozen`.** Nichts nach der Erstellung mutieren; für
  Änderungen `dataclasses.replace(obj, feld=…)` verwenden. Engines sammeln in
  lokalen Listen/Dicts und konstruieren das Ergebnis **einmalig am Ende**.
- **Caches/Registries** erben von `core.cache.Cache[T]` bzw.
  `core.registry.Registry[T]`. **Fehler** immer aus `core.exceptions`
  (`AlphaAIError`-Hierarchie), nie blankes `ValueError`/`KeyError`.

## Score Engine – Kurzüberblick für die Weiterarbeit

- Einstieg: `ScoreEngine.from_config()` erzeugt eine Engine mit Gewichten aus
  `knowledge/score_rules.toml` und allen Standard-Modellen.
- Bewertung: `engine.score(strategy_report, indicators, patterns, symbol,
  timeframe)` → `ScoreReport` mit einem `ScoreResult` je Hypothese.
- Ergebnis: `report.results`; `report.top(n)` sortiert nach Gesamtscore (reine
  Anzeige, **keine** Empfehlung). Jeder `ScoreResult` trägt die acht
  Komponenten in `component_scores` und alle Modellwerte in
  `metadata['model_scores']`.
- **Neues Score-Modell hinzufügen** (einziger erlaubter Weg):
  1. Datei in `scores/` anlegen, `BaseScoreModel` implementieren (`compute`),
     nur Komponenten/Kontext nutzen, kein anderes Modell.
  2. In `engines/score_registry.py::build_default_registry` registrieren.
  3. Abschnitt in `knowledge/score_rules.toml` ergänzen (Sektionsname =
     Modellname). Die Engine muss dafür **nicht** geändert werden.
  4. Eigene Testdatei `tests/test_score_<name>.py` anlegen.
- Neue **Komponenten** kommen in `scores/base.py::compute_components` hinzu und
  werden in `COMPONENT_NAMES` sowie den Gewichten des Weighted Score ergänzt.

## Wichtige Konventionen (unbedingt einhalten)

- **Keine hartcodierten Werte** – Gewichte in `knowledge/*.toml`, Einstellungen
  in `config/*.toml`. Komponenten-Formeln sind dokumentierte Messungen.
- **Type Hints und Docstrings** für jede öffentliche Funktion/Klasse.
- **Black- und Ruff-konform** (Zeilenlänge 100).
- **Abhängigkeiten zeigen nur nach unten**; kein Score-Modell/Strategie/Muster/
  Indikator hängt von einem anderen ab.
- **Kein Auto-Trading**, keine Entscheidung/Positionsgröße/Risiko in der Score
  Engine.
- Nach jedem Sprint: `PROJECT_STATUS.md`, `CHANGELOG.md`, `ROADMAP.md`,
  `AI_CONTEXT.md`, `DECISIONS.md` und diese Datei aktualisieren.

## Nächster geplanter Schritt

**Dashboard & Kalibrierung (geplant):** die Streamlit-Oberfläche, die die
fertigen Kennzahlen aus dem `AnalyticsResult` **nur visualisiert** (keine
Geschäftslogik); daneben Schwellen/Gewichte der Empfehlung an realen Daten
kalibrieren und die vorbereiteten Backtest-Kennzahlen annualisieren – weiterhin
ohne automatische Orderausführung und ohne Broker-API. Details in `ROADMAP.md`.
