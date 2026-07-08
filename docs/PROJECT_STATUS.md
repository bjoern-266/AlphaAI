# Projektstatus

_Wird nach jedem Sprint automatisch aktualisiert._

- **Datum:** 2026-07-08
- **Aktueller Sprint:** Sprint 5 – Pattern Engine
- **Status:** ✅ Abgeschlossen

## Was ist vorhanden

### Fundament (Sprint 1)

- Struktur, Konfiguration, Logging, Fehlerklassen, Wissensbasis, Basistests.

### Data Layer (Sprint 2)

- Provider, Repository, MarketDataEngine, Cache, Validator, Universen.

### Scanner Core (Sprint 3)

- ScanRequest/ScanResult/ScanReport, ScanStatistics, ScanPipeline,
  ScannerEngine, ScannerManager (reine Orchestrierung).

### Indicator Engine (Sprint 4)

- 11 unabhängige Indikatoren, Registry, Engine, Result, Cache.

### Pattern Engine (Sprint 5)

- **8 vollständig implementierte Muster** in `patterns/` (je eigene Datei):
  FVG, BOS, CHoCH, Equal Highs, Equal Lows, Liquidity Sweep, Market Structure,
  Trend Structure.
- **3 vorbereitete Muster** (ohne Erkennung): Order Block, Breaker Block,
  Mitigation Block.
- **FVG** erkennt bullish/bearish, fresh/partially_mitigated/mitigated,
  Gap-Größe, Gap-%, Kerzenindex, Timestamp und Preisbereich.
- **BOS/CHoCH** über gemeinsamen Struktur-Break-Helper (BOS = Fortsetzung,
  CHoCH = Trendwechsel).
- **Trend Structure** liefert Higher High/Low, Lower High/Low und Trend.
- **Registry** (`PatternRegistry`) als einzige Erweiterungsstelle.
- **Engine** (`PatternEngine`): Input `MarketResult`/OHLCV → Output
  `PatternReport` mit `PatternResult` je Muster (Name, Typ, Richtung,
  Strength 0-100, Confidence 0-1, Timestamp, Price Level, Metadata).
- **Cache** (`PatternCache`, FIFO).
- **Validierung**: genug Kerzen, ungültige Muster, überlappende Muster,
  ungültige Zeitreihen.
- **Parameter** ausschließlich aus `knowledge/pattern_rules.toml`.
- **Tests:** 197 gesamt (49 neue).

## Was ist bewusst NICHT vorhanden

- Keine Strategy-Engine, keine Score-Engine, keine Risk-Engine, keine
  Recommendation-Engine.
- Keine Handelsentscheidungen, keine Buy/Sell-Signale.
- Keine Dashboard-Logik.

Diese Teile folgen ab Sprint 6 (siehe `ROADMAP.md`).

## Qualitätsnachweis (Sprint 5)

| Prüfung | Ergebnis |
|---|---|
| pytest | 197 Tests bestanden |
| Ruff / Black | konform |
| Import-Zyklen | 0 (61 Module analysiert) |
| Muster-Unabhängigkeit | 0 Verstöße |
| SOLID-Heuristik (Muster) | 0 Verstöße |
| Testabdeckung (Pattern-Module) | 95 % |

## Nächster Schritt

Warten auf Freigabe für **Sprint 6** (z. B. Strategie-Engine auf Basis von
Indikator- und Muster-Ergebnissen).
