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

## Aktueller Stand

Sprint 1 (Fundament), Sprint 2 (Data Layer) und Sprint 3 (Scanner Core) sind
abgeschlossen. Es gibt weiterhin keine Indikatoren, keine Muster, keine Scores
und keine Handelslogik. Nächster Schritt: Sprint 4 (Analyse-Engines). Immer
zuerst `PROJECT_STATUS.md` und `HANDOVER.md` lesen.
