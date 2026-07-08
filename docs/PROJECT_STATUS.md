# Projektstatus

_Wird nach jedem Sprint automatisch aktualisiert._

- **Datum:** 2026-07-08
- **Aktueller Sprint:** Sprint 4 – Indicator Engine
- **Status:** ✅ Abgeschlossen

## Was ist vorhanden

### Fundament (Sprint 1)

- Struktur, Konfiguration, Logging, Fehlerklassen, Wissensbasis, Basistests.

### Data Layer (Sprint 2)

- Provider, Repository, MarketDataEngine, Cache, Validator, Universen,
  MarketRequest/MarketResult.

### Scanner Core (Sprint 3)

- ScanRequest/ScanResult/ScanReport, ScanStatistics, ScanPipeline,
  ScannerEngine, ScannerManager (reine Orchestrierung).

### Indicator Engine (Sprint 4)

- **11 unabhängige Indikatoren** in `indicators/` (je eigene Datei): EMA, RSI,
  ATR, VWAP, MACD, RelativeVolume, ADX, Bollinger, Stochastic, OBV,
  VolumeProfile.
- **Registry** (`IndicatorRegistry`) als einzige Erweiterungsstelle.
- **Engine** (`IndicatorEngine`): Orchestrierung, Validierung, optionaler Cache;
  Input `MarketResult`/OHLCV → Output `IndicatorResult`.
- **IndicatorResult**: volle Zeitreihen + typisierte Zugriffe (EMA20/50/200,
  RSI14, ATR14, VWAP, MACD/Signal/Histogramm, RelativeVolume, ADX,
  BollingerBands, Stochastic, OBV, VolumeProfile) sowie `calculation_time`,
  `valid`, `warnings`, `metadata`.
- **Cache** (`IndicatorCache`, FIFO) mit Treffer-/Fehltreffer-Zählung.
- **Parameter** ausschließlich aus `knowledge/indicator_rules.toml`.
- **Multi-Timeframe**: Architektur vorbereitet (Timeframe-Label), nicht
  implementiert.
- **Tests:** 148 gesamt (53 neue: je Indikator, Registry, Cache, Engine,
  Validierung, Performance).

## Was ist bewusst NICHT vorhanden

- Keine Muster (FVG, BOS, CHoCH, Order Blocks).
- Keine Score-Engine, keine Risk-Engine, keine Recommendation-Engine.
- Keine Kauf-/Verkaufssignale, keine Bewertung.
- Keine Dashboard-Logik.

Diese Teile folgen ab Sprint 5 (siehe `ROADMAP.md`).

## Qualitätsnachweis (Sprint 4)

| Prüfung | Ergebnis |
|---|---|
| pytest | 148 Tests bestanden |
| Ruff | keine Beanstandungen |
| Black | konform |
| Import-Zyklen | 0 (44 Module analysiert) |
| Indikator-Unabhängigkeit | 0 Verstöße |
| SOLID-Heuristik | 0 Verstöße |
| Testabdeckung (engines + indicators) | 92 % |

## Nächster Schritt

Warten auf Freigabe für **Sprint 5 – Muster & Strategien** (Patterns/Strategien
auf Basis der Indikatorergebnisse).
