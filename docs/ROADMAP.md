# Roadmap

_Wird laufend gepflegt._ Die Roadmap zeigt die geplante Reihenfolge der
Sprints. Jeder Sprint baut auf dem vorherigen auf und endet mit aktualisierter
Dokumentation.

## Sprint 1 – Fundament ✅ (abgeschlossen)

Projektstruktur, Konfiguration, Logging, Fehlerklassen, Wissensbasis,
Dokumentation, Basistests. Kein Scanner, keine Daten, keine Handelslogik.

## Sprint 2 – Datenquellen (geplant)

- Einheitliche Provider-Schnittstelle definieren.
- Marktdatenzugriff über yfinance (mit Zwischenspeicherung).
- Datenmodelle für Kursreihen in `data/` und `models/`.
- Tests für den Datenzugriff.

## Sprint 3 – Analyse-Engines (geplant)

- Technische Indikatoren über `engines/` (Parameter aus
  `knowledge/indicator_rules.toml`).
- Verwendung von pandas / pandas-ta.

## Sprint 4 – Muster & Strategien (geplant)

- Kursmuster in `patterns/` (Regeln aus `pattern_rules.toml`).
- Setup-Bewertung in `strategies/` (Regeln aus `strategy_rules.toml`).
- Scanner in `scanner/` zur Orchestrierung.

## Sprint 5 – Dashboard (geplant)

- Streamlit-Oberfläche in `dashboard/`.
- Charts mit Plotly.
- Anzeige der Empfehlungen mit Begründung.

## Sprint 6 – Persistenz & Lernfähigkeit (geplant)

- Speicherung von Analysen/Empfehlungen in SQLite (`database/`).
- Nachkontrolle der Empfehlungen und Auswertung.
- Rückspielung der Erkenntnisse in `knowledge/journal.md`.

## Sprint 7 – API (geplant)

- FastAPI-Schnittstelle, um Analysen programmatisch abzurufen.

> Reihenfolge und Umfang können sich anpassen. Änderungen werden hier und in
> `CHANGELOG.md` dokumentiert.
