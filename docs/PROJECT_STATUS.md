# Projektstatus

_Wird nach jedem Sprint automatisch aktualisiert._

- **Datum:** 2026-07-08
- **Aktueller Sprint:** Sprint 3 – Scanner Core
- **Status:** ✅ Abgeschlossen

## Was ist vorhanden

### Fundament (Sprint 1)

- Modulare Projektstruktur, Konfiguration, Logging, Fehlerklassen,
  Wissensbasis, Dokumentation, Basistests.

### Data Layer (Sprint 2)

- Provider (`BaseProvider`, `YahooProvider`; Finnhub/Polygon/AlphaVantage/IEX
  vorbereitet), `MarketRepository`, `MarketDataEngine`, `TTLCache`, Validator,
  Universen, `MarketRequest`/`MarketResult`.

### Scanner Core (Sprint 3)

- **Anfrage/Ergebnis:** `ScanRequest` (Markt, Universum, Symbole, Provider,
  Timeframe, Interval, UseCache, RequestedFeatures, MaxWorkers) und `ScanResult`
  je Symbol (Ticker, Provider, Markt, Timeframe, Timestamp, Status,
  RawMarketData, Metadata, Error) mit **vorbereiteten, leeren** Analysefeldern
  (Indicators, Patterns, Score, Risk, Recommendation).
- **Pipeline:** `ScanPipeline` orchestriert (Universum laden → MarketDataEngine
  aufrufen → Daten sammeln → ScanResult erzeugen), ohne jegliche Analyse.
- **Engine:** `ScannerEngine` kennt ausschließlich die Pipeline; übernimmt das
  Scan-Logging.
- **Manager:** `ScannerManager` bereitet Läufe über mehrere Märkte/Universen/
  Zeiträume vor (sequenziell, keine Parallelisierung).
- **Statistik:** `ScanStatistics` erfasst Start-/Endzeit, Laufzeit, Symbolzahl,
  Provider, Cache-Treffer/-Fehltreffer und Fehler.
- **Konfiguration:** neuer `[scanner]`-Bereich (max_workers, requested_features)
  – ausschließlich aus TOML.
- **Tests:** 95 Tests gesamt (27 neue für den Scanner Core).

## Was ist bewusst NICHT vorhanden

- Keine Indikatoren (EMA, RSI, ATR, VWAP, MACD).
- Keine Muster (FVG, BOS, CHoCH).
- Keine Scores, keine Bewertung, keine Buy/Sell-Signale.
- Keine Dashboard-Ansicht.

Diese Teile folgen ab Sprint 4 (siehe `ROADMAP.md`).

## Qualitätsnachweis (Sprint 3)

| Prüfung | Ergebnis |
|---|---|
| pytest  | 95 Tests bestanden |
| Ruff    | keine Beanstandungen |
| Black   | konform |
| E2E-Rauchtest | Manager → Engine → Pipeline → Data Layer erzeugt ScanResults |

## Nächster Schritt

Warten auf Freigabe für **Sprint 4 – Analyse-Engines / Indikatoren** auf Basis
der im `ScanResult` bereitgestellten Rohdaten.
