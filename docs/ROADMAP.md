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

## Sprint 6 – Strategy Engine ✅ (abgeschlossen)

- 5 unabhängige Strategien in `strategies/` (FVG, Trend Following, Momentum,
  Breakout, Mean Reversion), die Indikatoren und Muster zu Hypothesen
  kombinieren.
- `StrategyRegistry` (einzige Erweiterungsstelle), `StrategyEngine`,
  `StrategyResult`/`StrategyReport`, `StrategyCache`.
- Parameter aus `knowledge/strategy_rules.toml`.
- 50 neue Tests (247 gesamt), Testabdeckung Strategy-Module 96 %.
- Nur Hypothesen; keine Scores, keine Kauf-/Verkaufsentscheidung.

## Sprint 7 – Score Engine ✅ (abgeschlossen)

- 5 unabhängige Score-Modelle in `scores/` (weighted, confidence, quality,
  consensus, market) und 8 separat gespeicherte Komponenten.
- `ScoreRegistry` (einzige Erweiterungsstelle), `ScoreEngine`,
  `ScoreResult`/`ScoreReport`, `ScoreCache`.
- Vollständig transparente Scores (Komponenten-Aufschlüsselung).
- Gewichte aus `knowledge/score_rules.toml`.
- 60 neue Tests (307 gesamt), Testabdeckung Score-Module 96 %.
- Nur Scores; keine Entscheidung, keine Positionsgröße, kein Risiko.

## Sprint 8 – Risk Engine (geplant)

- Ableitung von Risiko und Positionsgröße aus den Scores (Regeln aus
  `knowledge/risk.md`/TOML).
- Anbindung der Ergebnisse an den Scanner.

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
