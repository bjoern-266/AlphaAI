# Projektstatus

_Wird nach jedem Sprint automatisch aktualisiert._

- **Datum:** 2026-07-09
- **Aktueller Sprint:** Sprint 9 – Recommendation Engine
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

- 5 Strategien, Registry, Engine, Result, Cache (nur Hypothesen).

### Score Engine (Sprint 7)

- **5 Score-Modelle** in `scores/` (je eigene Datei): `weighted_score`,
  `confidence_score`, `quality_score`, `consensus_score`, `market_score`.
- **8 Komponenten** (separat gespeichert): Trend, Momentum, Pattern Strength,
  Pattern Confidence, Indicator Quality, Market Context, Volume Quality,
  Data Quality.
- **ScoreResult**: Score ID, Strategy Name, Hypothesis ID, Total Score (0-100),
  Confidence (0-1), Quality/Consensus/Market Score, Component Scores, Reasons,
  Warnings, Metadata, Timestamp.
- **Transparenz**: jeder Score über Komponenten erklärbar (z. B. `trend: 18/20`).
- **ScoreEngine**: Input `StrategyReport` (+ Indikatoren/Muster für Komponenten)
  → `ScoreReport`.
- **Registry** (`ScoreRegistry`) als einzige Erweiterungsstelle.
- **Cache** (`ScoreCache`, FIFO).
- **Validierung**: fehlende Hypothesen, ungültige Gewichte, Gewichte ≠ 100 %,
  fehlende Komponenten.
- **Gewichte** ausschließlich aus `knowledge/score_rules.toml`.
- **Tests:** 307 gesamt (60 neue).

### Architecture Consolidation (Sprint 7.5)

Verhaltenserhaltender Umbau (kein neues Feature):

- **Entities-Schicht `models/`** bündelt alle Ergebnis-/Datentypen
  (`market`, `indicator`, `pattern`, `strategy`, `score`; `risk`/
  `recommendation` vorbereitet). Alte Importpfade bleiben als Re-Exports gültig.
- **Alle Ergebnisobjekte sind unveränderlich** (`frozen`); Engines konstruieren
  einmalig am Ende und nutzen `dataclasses.replace()` für die Rechenzeit.
- **Generische `Cache[T]`/`Registry[T]`** in `core/`; die Engine-Varianten sind
  dünne Spezialisierungen. **Einheitliche Exception-Hierarchie** unter
  `AlphaAIError`.
- **Kopplung reduziert:** `strategies`/`scores` importieren nichts mehr aus
  `engines`. Prüfskript `scripts/quality_check.py` fest im Test verankert.
- **Tests:** 335 gesamt (28 neue; bestehende unverändert).

### Risk Engine (Sprint 8)

- **8 unabhängige Risk-Modelle** in `risk/` (je eigene Datei): `position_sizing`,
  `volatility_risk`, `liquidity_risk`, `gap_risk`, `market_risk`,
  `correlation_risk`, `portfolio_risk`, `execution_risk`. Gemeinsame
  Schnittstelle/Helfer in `risk/base.py`; kein Modell hängt von einem anderen ab.
- **10 Risikokomponenten** (getrennt, erklärbar): Volatilität, Liquidität, Gap,
  Spread, ATR, Markt, Korrelation, Portfolio-Exposure, Datenqualität, News
  (News vorbereitet/neutral).
- **RiskResult** mit Overall Risk (0-100), Risk Level (LOW/MEDIUM/HIGH),
  Positionsgröße, Stückzahl/Orderwert/Slippage/Kommission, Stop-/Take-Profit-
  Abstand, CRV, Komponenten, Reasons/Warnings.
- **RiskEngine**: Input `ScoreReport` (+ Indikatoren/Rohdaten) → `RiskReport`.
  `RiskRegistry` (einzige Erweiterungsstelle), `RiskCache` (FIFO).
- **Positionsgröße** aus `settings.toml` (Depot, Fractional Shares, Risiko/Trade,
  max. Positionen); Ausführungskosten/Schwellen aus `knowledge/risk_rules.toml`.
- **Portfolio-Risiko vorbereitet** (offene Positionen werden durchgereicht).
- **Validierung**: fehlende Scores, negative Depotgröße, ungültige ATR/Preise,
  ungültige Positionsgrößen/Risk-Reward.
- **Tests:** 413 gesamt (76 neue).

### Recommendation Engine (Sprint 9)

- **5 unabhängige Modelle** in `recommendation/` (je eigene Datei):
  `decision_model`, `recommendation_model`, `confidence_model`, `summary_model`,
  `explanation_model`. Gemeinsame Logik in `recommendation/base.py`.
- **6 Entscheidungsfaktoren** (Strategie, Score, Risiko, Konsens, Marktqualität,
  Datenqualität) → Gesamtrating 0-100 → Stufe (STRONG_BUY/BUY/WATCH/WAIT/AVOID)
  + Handlung (OPEN/WAIT/MONITOR/SKIP).
- **No-Trade-Philosophie:** Der Score-Anteil ist begrenzt, Konsens belohnt
  Breite, und Gates deckeln bei Risiko/geringem Konsens/schwacher Datenqualität
  – ein hoher Score allein führt nie zu BUY. `WAIT`/`AVOID` sind vollwertig.
- **RecommendationEngine**: Input `StrategyReport` + `ScoreReport` +
  `RiskReport` → `RecommendationReport`. `RecommendationRegistry` (einzige
  Erweiterungsstelle), `RecommendationCache` (FIFO).
- **Erklärbarkeit:** jede Empfehlung mit Reasons, Warnings, Summary – keine
  Blackbox. Regeln ausschließlich aus `knowledge/recommendation_rules.toml`.
- **Validierung:** fehlender/ungültiger Strategy-/Score-/Risk-Report, fehlende
  Zuordnung, ungültige Level/Confidence/Ratings.
- **Tests:** 502 gesamt (89 neue).

## Was ist bewusst NICHT vorhanden

- Keine Dashboard-Logik, keine Broker-API, keine automatische Orderausführung,
  keine Paper-Trading-Funktionen.
- Keine Positionseröffnung, keine Order. Die Recommendation Engine liefert
  ausschließlich `RecommendationResult`.

Diese Teile folgen in späteren Sprints (siehe `ROADMAP.md`).

## Qualitätsnachweis (Sprint 9)

| Prüfung | Ergebnis |
|---|---|
| pytest | 502 Tests bestanden |
| Ruff / Black | konform |
| Import-Zyklen | 0 |
| Entities-Schicht `models/` | 0 Verstöße |
| Plugin-Unabhängigkeit (inkl. Recommendation) | 0 Verstöße |
| SOLID-Heuristik (inkl. Recommendation) | 0 Verstöße |
| Ergebnisobjekte unveränderlich (`frozen`) | vollständig |

## Nächster Schritt

Warten auf Freigabe für den nächsten Sprint (z. B. **Dashboard** oder
**End-to-End-Verdrahtung im Scanner**) – weiterhin ohne automatische
Orderausführung und ohne Broker-API.
