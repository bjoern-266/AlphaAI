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

## Sprint 3 – Analyse-Engines (geplant)

- Technische Indikatoren über `engines/` (Parameter aus
  `knowledge/indicator_rules.toml`).
- Verwendung von pandas / pandas-ta auf Basis der Data Layer.

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
