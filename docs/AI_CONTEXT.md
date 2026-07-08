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
{engines, patterns, strategies} → {data, providers} → database → core`.
Details in `ARCHITECTURE.md`.

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

## Aktueller Stand

Sprint 1–6 sind abgeschlossen (Fundament, Data Layer, Scanner Core, Indicator
Engine, Pattern Engine, Strategy Engine). Es gibt weiterhin keine Score-/Risk-/
Recommendation-Engine und keine Handelslogik. Nächster Schritt: Sprint 7 (Score
Engine). Immer zuerst `PROJECT_STATUS.md` und `HANDOVER.md` lesen.
