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

## Aktueller Stand

Sprint 1 (Fundament) ist abgeschlossen. Es gibt noch keinen Scanner, keine
Datenquellen, keine Indikatoren und keine Handelslogik. Nächster Schritt:
Sprint 2 (Datenquellen). Immer zuerst `PROJECT_STATUS.md` und `HANDOVER.md`
lesen.
