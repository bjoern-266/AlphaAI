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

## Sprint 3 – Scanner Core ✅ (abgeschlossen)

- `ScanRequest`/`ScanResult`/`ScanReport` und `ScanStatistics`.
- `ScanPipeline` (reine Orchestrierung), `ScannerEngine` (kennt nur die
  Pipeline), `ScannerManager` (Mehrfach-Scans, sequenziell).
- Cache-Statistik über `metadata["cache_hit"]`; neuer `[scanner]`-Config-Bereich.
- 27 neue Tests (95 gesamt). Keine Indikatoren, Muster, Scores oder Signale.

## Sprint 4 – Indicator Engine ✅ (abgeschlossen)

- 11 unabhängige Indikatoren in `indicators/` (je eigene Datei).
- `IndicatorRegistry` (einzige Erweiterungsstelle), `IndicatorEngine`,
  `IndicatorResult`, `IndicatorCache`.
- Parameter aus `knowledge/indicator_rules.toml`; Multi-Timeframe vorbereitet.
- 53 neue Tests (148 gesamt), Testabdeckung neuer Module 92 %.
- Keine Muster, keine Scores, keine Signale.

## Sprint 5 – Pattern Engine ✅ (abgeschlossen)

- 11 unabhängige Muster in `patterns/` (8 implementiert, 3 vorbereitet).
- `PatternRegistry` (einzige Erweiterungsstelle), `PatternEngine`,
  `PatternResult`/`PatternReport`, `PatternCache`.
- Parameter aus `knowledge/pattern_rules.toml`.
- 49 neue Tests (197 gesamt), Testabdeckung Pattern-Module 95 %.
- Keine Scores, keine Signale, keine Handelsentscheidungen.

## Sprint 6 – Strategien (geplant)

- Setup-Bewertung in `strategies/` (Regeln aus `strategy_rules.toml`) auf Basis
  von Indikator- und Muster-Ergebnissen.
- Anbindung von Indikator-/Muster-Ergebnissen an den Scanner
  (`ScanResult.indicators`/`.patterns`).

## Sprint 6 – Dashboard (geplant)

- Streamlit-Oberfläche in `dashboard/`.
- Charts mit Plotly.
- Anzeige der Empfehlungen mit Begründung.

## Sprint 7 – Persistenz & Lernfähigkeit (geplant)

- Speicherung von Analysen/Empfehlungen in SQLite (`database/`).
- Nachkontrolle der Empfehlungen und Auswertung.
- Rückspielung der Erkenntnisse in `knowledge/journal.md`.

## Sprint 8 – API (geplant)

- FastAPI-Schnittstelle, um Analysen programmatisch abzurufen.

> Reihenfolge und Umfang können sich anpassen. Änderungen werden hier und in
> `CHANGELOG.md` dokumentiert.
