# AI-Kontext

_Diese Datei wird laufend gepflegt und richtet sich an KI-Modelle, die später
am Projekt mitarbeiten._ Sie fasst den festen Rahmen zusammen, damit ein Modell
ohne Chatverlauf korrekt handeln kann.

## Was ist Alpha AI

Eine modulare **Daytrading-Analyseplattform**. Sie **analysiert** Märkte und
erzeugt **nachvollziehbare Empfehlungen**. Sie **handelt nicht automatisch**.

## Wichtigster Kontext über den Auftraggeber

Der Auftraggeber besitzt **keine Programmierkenntnisse**. Deshalb gilt:

- Sauber, modular und verständlich entwickeln.
- Jede Entscheidung erklären und dokumentieren.
- Nach jedem Sprint die Dokumentation aktualisieren.
- Es darf **nie** Projektwissen geben, das nur im Chat existiert.

## Technischer Rahmen

- **Sprache:** Python 3.12.
- **Stack:** FastAPI, Streamlit, SQLite, Plotly, yfinance, pandas, numpy,
  pandas-ta, pytest, TOML.
- **Standards:** Type Hints, Docstrings, Black- und Ruff-konform, SOLID,
  Clean Architecture, Dependency Injection vorbereitet.
- **Verboten:** hartcodierte Werte, Dummy-Funktionen, Platzhalter,
  TODO-Kommentare ohne Beschreibung.
- **Prinzip:** Lieber weniger Code, aber sauber.

## Architektur in einem Satz

Schichten mit Abhängigkeiten nur nach unten: `dashboard → scanner →
{engines, patterns, strategies} → {data, providers} → database →
models → core`.
Details in `ARCHITECTURE.md`.

## Konsolidiertes Fundament (ab Sprint 7.5, Tag `v0.1.0-foundation`)

Verbindliche Regeln für jede Weiterarbeit:

- **Datentypen gehören in `models/`** (Entities-Schicht, importiert nichts aus
  höheren Schichten): `market`, `indicator`, `pattern`, `strategy`, `score`;
  `risk`/`recommendation` sind vorbereitet. Alte Importpfade
  (`data.market_result`, `engines.*_result`, `*/base.py`) bleiben als
  Re-Exports gültig – Engines und `*/base.py` enthalten **nur** Logik.
- **Alle Ergebnisobjekte sind unveränderlich (`frozen`).** Nie nach der
  Erstellung mutieren; Engines sammeln in lokalen Akkumulatoren und
  konstruieren einmalig am Ende, Änderungen via `dataclasses.replace()`.
- **Caches/Registries** erben von `core.cache.Cache[T]` /
  `core.registry.Registry[T]`. **Fehler** nur aus der `AlphaAIError`-Hierarchie
  in `core.exceptions` – kein blankes `ValueError`/`KeyError` für Fachfehler.
- **Prüfen vor jedem Commit:** `python scripts/quality_check.py` (0 Zyklen,
  0 Verstöße) und `pytest`.

## Wo liegt was

- Einstellbare Parameter: `config/settings.toml`.
- Analyse-Regeln/Parameter: `knowledge/*.toml`, Erklärungen: `knowledge/*.md`.
- Technische Grundlagen: `core/`.
- Dokumentation & Historie: `docs/`.

## Data Layer (ab Sprint 2 verfügbar)

Zugriff auf Marktdaten immer über die `MarketDataEngine`
(`data/market_data_engine.py`). Kette: `Engine → Repository → Provider`, mit
`Cache` und `Validator` im Repository. Ergebnis ist ein `MarketResult` mit
kanonischem Schema (`open, high, low, close, adj_close, volume`). Objekte via
`repositories.repository_factory.build_repository(settings)` erzeugen. Neue
Datenquellen: `BaseProvider` implementieren und in der `provider_factory`
registrieren. Symbollisten ausschließlich in `config/universe.toml`.

## Scanner Core (ab Sprint 3 verfügbar)

Reine Orchestrierung, keine Analyse. Kette: `ScannerManager → ScannerEngine →
ScanPipeline → MarketDataEngine`. `ScannerEngine` kennt nur die Pipeline. Ein
Scan liefert ein `ScanReport` mit `ScanResult` je Symbol; dessen Analysefelder
(`indicators`, `patterns`, `score`, `risk`, `recommendation`) sind vorbereitet
und leer. Anfragen über `build_scan_request(settings, ...)`. Der spätere
Analysecode befüllt die vorbereiteten Felder, ohne den Scanner umzubauen.

## Indicator Engine (ab Sprint 4 verfügbar)

Berechnet technische Indikatoren, trifft aber keine Entscheidungen und erzeugt
keine Scores/Signale. Kette: `MarketData → IndicatorEngine → IndicatorResult`.
Jeder Indikator liegt in `indicators/<name>.py`, ist unabhängig und wird nur
über die `IndicatorRegistry` (`engines/indicator_registry.py`) ergänzt.
Parameter ausschließlich aus `knowledge/indicator_rules.toml`. Einstieg:
`IndicatorEngine.from_config()`. Multi-Timeframe ist vorbereitet, nicht
implementiert.

## Pattern Engine (ab Sprint 5 verfügbar)

Erkennt Chartmuster, trifft aber keine Entscheidungen und erzeugt keine
Scores/Signale. Kette: `IndicatorResult → PatternEngine → PatternReport`. Jedes
Muster liegt in `patterns/<name>.py`, ist unabhängig und wird nur über die
`PatternRegistry` (`engines/pattern_registry.py`) ergänzt. Ergebnistypen
(`PatternResult`) liegen in `patterns/base.py` (vermeidet Import-Zyklen).
Parameter ausschließlich aus `knowledge/pattern_rules.toml`. Einstieg:
`PatternEngine.from_config()`. 8 Muster implementiert (FVG, BOS, CHoCH, Equal
Highs/Lows, Liquidity Sweep, Market/Trend Structure), 3 vorbereitet (Order/
Breaker/Mitigation Block).

## Strategy Engine (ab Sprint 6 verfügbar)

Kombiniert Indikatoren und Muster zu objektiven Hypothesen, trifft aber keine
Kauf-/Verkaufsentscheidung und vergibt keinen Gesamtscore. Kette:
`IndicatorResult + PatternReport → StrategyEngine → StrategyReport`. Jede
Strategie liegt in `strategies/<name>.py`, ist unabhängig und wird nur über die
`StrategyRegistry` (`engines/strategy_registry.py`) ergänzt. Ergebnistypen
(`StrategyResult`) liegen in `strategies/base.py` (vermeidet Import-Zyklen).
Parameter ausschließlich aus `knowledge/strategy_rules.toml`. Einstieg:
`StrategyEngine.from_config()`. 5 Strategien: fvg_strategy, trend_following,
momentum_strategy, breakout_strategy, mean_reversion.

## Score Engine (ab Sprint 7 verfügbar)

Bewertet jede Hypothese objektiv, trifft aber keine Entscheidung, erzeugt keine
Positionsgröße und kein Risiko. Kette: `StrategyReport → ScoreEngine →
ScoreReport`. Fünf unabhängige Modelle in `scores/<name>.py` (weighted,
confidence, quality, consensus, market), acht separat gespeicherte Komponenten.
Ergebnistypen liegen in `engines/score_result.py`, Komponenten/Validierung in
`scores/base.py`. Neue Modelle nur über die `ScoreRegistry`
(`engines/score_registry.py`); die Engine bleibt unverändert. Gewichte
ausschließlich aus `knowledge/score_rules.toml`. Einstieg:
`ScoreEngine.from_config()`. Jeder Score ist über seine Komponenten vollständig
erklärbar.

## Risk Engine (ab Sprint 8 verfügbar)

Bewertet das Risiko jeder Hypothese und empfiehlt eine Positionsgröße – **keine**
Kauf-/Verkaufsentscheidung, **keine** Position, **keine** Order. Kette:
`ScoreReport → RiskEngine → RiskReport`. Acht unabhängige Modelle in
`risk/<name>.py` (position_sizing, volatility, liquidity, gap, market,
correlation, portfolio, execution); zehn separat gespeicherte, erklärbare
Komponenten (News vorbereitet/neutral). Ergebnistypen liegen in `models/risk.py`
(re-exportiert über `engines/risk_result.py`), gemeinsame Helfer/Positionsgröße
in `risk/base.py`. Neue Modelle nur über die `RiskRegistry`
(`engines/risk_registry.py`); die Engine bleibt unverändert. Modellparameter,
Gewichte und Schwellen ausschließlich aus `knowledge/risk_rules.toml`;
Konto-/Depotwerte (Depot, Fractional Shares, Risiko/Trade, max. Positionen)
ausschließlich aus `config/settings.toml`. Portfolio-Risiko ist vorbereitet
(offene Positionen werden an die Modelle durchgereicht). Einstieg:
`RiskEngine.from_config()`.

## Recommendation Engine (ab Sprint 9 verfügbar)

Letzte fachliche Entscheidungsschicht: kombiniert `StrategyReport`,
`ScoreReport` und `RiskReport` je Hypothese zu einer objektiven, vollständig
erklärbaren Empfehlung. Kette: `Strategy+Score+Risk → RecommendationEngine →
RecommendationReport`. Fünf unabhängige Modelle in `recommendation/<name>.py`
(decision, recommendation, confidence, summary, explanation); sechs
Entscheidungsfaktoren (Strategie, Score, Risiko, Konsens, Marktqualität,
Datenqualität). **Richtung und Stärke sind getrennt (ab 9.6):** `direction`
(LONG/SHORT/NEUTRAL) und `recommendation_strength` (VERY_HIGH/HIGH/MEDIUM/LOW/
REJECT); dazu Handlungen OPEN/WAIT/MONITOR/SKIP. Die Stärke impliziert nie eine
Richtung – ein bärisches Setup ist SHORT, nie „BUY". **No-Trade-Philosophie:**
Score-Anteil begrenzt, Konsens belohnt Breite, Gates deckeln bei Risiko/geringem
Konsens/schwacher Datenqualität – ein hoher Score allein führt nie zu hoher
Stärke; `LOW`/`REJECT` sind vollwertig. Ergebnistypen in
`models/recommendation.py` (re-exportiert über
`engines/recommendation_result.py`), Logik/Helfer in `recommendation/base.py`.
Neue Modelle nur über die `RecommendationRegistry`; Regeln ausschließlich aus
`knowledge/recommendation_rules.toml`. Einstieg:
`RecommendationEngine.from_config()`. Jede Empfehlung ist über Reasons/Warnings/
Summary vollständig erklärbar (keine Blackbox). **Keine** Order, **keine**
Broker-Anbindung.

## Gesamtpipeline (ab Sprint 9.5 verdrahtet)

Die komplette Kette ist über den `IntegrationRunner` (`pipeline/runner.py`)
End-to-End verbunden: `MarketData → Indicator → Pattern → Strategy → Score →
Risk → Recommendation`. Ergebnis je Symbol ist ein `PipelineResult`
(`models/pipeline.py`, frozen). `pipeline.consistency.verify_pipeline` prüft,
dass jede Empfehlung genau einen Risk-, jeder Risk genau einen Score- und jeder
Score genau einen Strategy-Result hat (IDs eindeutig, Referenzen gültig).
Datenfluss: `docs/PIPELINE.md`; Validierung/Auffälligkeiten:
`docs/VALIDATION_REPORT.md`. Der Runner enthält **keine** neue Fachlogik.

## Backtesting-Framework (ab Sprint 10 verfügbar)

**Rein bewertend**: lässt historische Marktdaten durch die **bestehende**
Pipeline laufen und misst, wie sich die daraus entstehenden Empfehlungen
entwickelt hätten. **Keine** neue Handelsregel, **keine** Änderung an einer
Engine, **keine** echte Order (Trades werden ausschließlich rechnerisch
simuliert). Kette: `Historische Marktdaten → bestehende Pipeline →
BacktestEngine → BacktestReport`. Subsystem `backtesting/`
(`historical_runner` – kein Look-Ahead; `trade_simulator` – Entry/Exit/Stop/
Take-Profit, Fractional Shares, Kosten; `performance_metrics`; `equity_curve`;
`statistics` – Sharpe/Sortino/Calmar **vorbereitet**; `benchmark` – Buy & Hold;
`base` + vier Modelle). Ergebnistypen in `models/backtest.py` (re-exportiert
über `engines/backtest_result.py`). Neue Backtest-Modelle nur über die
`BacktestRegistry`; Parameter ausschließlich aus `knowledge/backtest_rules.toml`,
Konto-/Risikowerte ausschließlich aus `config/settings.toml` (über die Risk
Engine). Einstieg: `BacktestEngine.from_config()`. Jeder simulierte Trade ist
vollständig nachvollziehbar. Datenfluss/Details: `docs/BACKTESTING.md`.

## Aktueller Stand

Sprint 1–10 sind abgeschlossen (Fundament, Data Layer, Scanner Core, Indicator
Engine, Pattern Engine, Strategy Engine, Score Engine, Architecture Consolidation,
Risk Engine, Recommendation Engine, End-to-End-Integration & Validierung,
Historical Backtesting Framework). Es gibt bewusst weiterhin **keine**
Dashboard-Logik, **keine** Broker-API, **keine** automatische Orderausführung und
**keine** Paper-Trading-Funktionen. Offene fachliche Kalibrierung (Schwellen an
realen Daten, Annualisierung der vorbereiteten Backtest-Kennzahlen) ist im
Validation Report festgehalten. Immer zuerst `PROJECT_STATUS.md` und
`HANDOVER.md` lesen.
