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

## Aktueller Stand

Sprint 1–8 sind abgeschlossen (Fundament, Data Layer, Scanner Core, Indicator
Engine, Pattern Engine, Strategy Engine, Score Engine, Architecture Consolidation,
Risk Engine). Es gibt weiterhin **keine** Recommendation-Engine, **keine**
Dashboard-Logik, **keine** Broker-API und **keine** automatische Orderausführung.
Nächster Schritt: Recommendation Engine. Immer zuerst `PROJECT_STATUS.md` und
`HANDOVER.md` lesen.
