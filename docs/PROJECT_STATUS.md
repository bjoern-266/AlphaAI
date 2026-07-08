# Projektstatus

_Wird nach jedem Sprint automatisch aktualisiert._

- **Datum:** 2026-07-08
- **Aktueller Sprint:** Sprint 6 – Strategy Engine
- **Status:** ✅ Abgeschlossen

## Was ist vorhanden

### Fundament (Sprint 1)

- Struktur, Konfiguration, Logging, Fehlerklassen, Wissensbasis, Basistests.

### Data Layer (Sprint 2)

- Provider, Repository, MarketDataEngine, Cache, Validator, Universen.

### Scanner Core (Sprint 3)

- ScanRequest/ScanResult/ScanReport, ScanStatistics, ScanPipeline,
  ScannerEngine, ScannerManager.

### Indicator Engine (Sprint 4)

- 11 unabhängige Indikatoren, Registry, Engine, Result, Cache.

### Pattern Engine (Sprint 5)

- 11 Muster (8 implementiert, 3 vorbereitet), Registry, Engine, Result, Cache.

### Strategy Engine (Sprint 6)

- **5 vollständig implementierte Strategien** in `strategies/` (je eigene
  Datei): `fvg_strategy`, `trend_following`, `momentum_strategy`,
  `breakout_strategy`, `mean_reversion`.
- **Jede Strategie** besitzt Name, Beschreibung, Version, Konfiguration,
  Pattern-Anforderungen, Indikator-Anforderungen und Confidence.
- **StrategyResult**: Strategy Name, Hypothesis ID, Richtung (bullish/bearish/
  neutral), Confidence (0-1), Strength (0-100), Matched Indicators, Matched
  Patterns, Reasons, Warnings, Metadata, Timestamp.
- **StrategyEngine**: Input `IndicatorResult` + `PatternReport` (+ optionale
  Rohdaten) → `StrategyReport` mit Hypothesen.
- **Registry** (`StrategyRegistry`) als einzige Erweiterungsstelle.
- **Cache** (`StrategyCache`, FIFO).
- **Validierung**: fehlende Daten, fehlende Muster, fehlende Indikatoren,
  inkonsistente Ergebnisse.
- **Parameter** ausschließlich aus `knowledge/strategy_rules.toml`.
- **Tests:** 247 gesamt (50 neue).

## Was ist bewusst NICHT vorhanden

- Keine Score-Engine, keine Risk-Engine, keine Recommendation-Engine.
- Keine Kauf-/Verkaufsentscheidung, kein Gesamtscore.
- Keine Dashboard-Logik.

Diese Teile folgen ab Sprint 7 (siehe `ROADMAP.md`).

## Qualitätsnachweis (Sprint 6)

| Prüfung | Ergebnis |
|---|---|
| pytest | 247 Tests bestanden |
| Ruff / Black | konform |
| Import-Zyklen | 0 (72 Module analysiert) |
| Strategie-Unabhängigkeit | 0 Verstöße |
| SOLID-Heuristik (Strategien) | 0 Verstöße |
| Testabdeckung (Strategy-Module) | 96 % |

## Nächster Schritt

Warten auf Freigabe für **Sprint 7 – Score Engine** (aggregiert die Hypothesen
zu einem Gesamtscore).
