# Projektstatus

_Wird nach jedem Sprint automatisch aktualisiert._

- **Datum:** 2026-07-10
- **Aktueller Sprint:** Sprint 11 – Paper Trading Framework
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
  Datenqualität) → Gesamtrating 0-100 → **Stärke** (VERY_HIGH/HIGH/MEDIUM/LOW/
  REJECT) + **Richtung** (LONG/SHORT/NEUTRAL, getrennt seit 9.6) + Handlung
  (OPEN/WAIT/MONITOR/SKIP).
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

### End-to-End-Integration (Sprint 9.5)

- **IntegrationRunner** (`pipeline/runner.py`) verkettet die komplette Pipeline
  `MarketData → Indicator → Pattern → Strategy → Score → Risk → Recommendation`.
  Keine neue Fachlogik, keine Umgehung von Schichten.
- **PipelineResult** (`models/pipeline.py`, `frozen`) bündelt alle Stufen.
- **Konsistenzprüfung** (`pipeline/consistency.py`): jede Empfehlung → genau ein
  Risk → genau ein Score → genau eine Strategie; IDs eindeutig, Referenzen gültig.
- **13 echte Szenarien** + **180 Integrations-Tests** (kein Mock): 0
  Konsistenzverstöße, alle Entscheidungs-Invarianten bestätigt.
- **Reports:** `docs/PIPELINE.md`, `docs/VALIDATION_REPORT.md` (mit
  Auffälligkeiten und Verbesserungsvorschlägen; keine Engine geändert).
- **Tests:** 682 gesamt (180 neue).

### Recommendation Semantics (Sprint 9.6)

- **Richtung und Qualität getrennt:** `RecommendationResult` trägt `direction`
  (LONG/SHORT/NEUTRAL) **und** `recommendation_strength` (VERY_HIGH … REJECT).
  Die Stärke impliziert nie mehr BUY/SELL/LONG/SHORT.
- Der 9.5-Befund „bärisches Setup → STRONG_BUY" ist **behoben**
  (`trend_down` → SHORT/VERY_HIGH). Bewertungslogik unverändert (Ratings
  identisch), nur Semantik/Benennung.
- **Tests:** 713 gesamt.

### Historical Backtesting Framework (Sprint 10)

- **Rein bewertend:** historische Marktdaten laufen durch die **bestehende**
  Pipeline; das Framework misst, wie sich die daraus entstehenden Empfehlungen
  entwickelt hätten. **Keine** neue Handelsregel, **keine** Änderung an einer
  Engine, **keine** echte Order (nur Simulation).
- **Subsystem `backtesting/`:** `historical_runner` (fensterweise, **kein**
  Look-Ahead), `trade_simulator` (Entry/Exit/Stop/Take-Profit, Fractional Shares,
  Kosten, eine Position zur Zeit, Stop hat bei Doppel-Treffer Vorrang),
  `performance_metrics`, `equity_curve`, `statistics` (Sharpe/Sortino/Calmar
  **vorbereitet**), `benchmark` (Buy & Hold), `base` + 4 Modelle.
- **Engine-Anbindung:** `BacktestEngine` (Input `MarketResult`/DataFrame →
  `BacktestReport`/`BacktestResult`), `BacktestRegistry` (einzige
  Erweiterungsstelle), `BacktestCache` (FIFO), Re-Export `backtest_result`.
- **BacktestResult:** ID, Symbol, Timeframe, Start/Ende, Anzahl Signale/Trades,
  Win/Loss Rate, Profit Factor, Ø Gewinn/Verlust, Ø CRV, Ø Haltedauer, Max
  Drawdown, Expectancy, Sharpe/Sortino/Calmar (vorbereitet), Equity Curve,
  Trade-Liste, Benchmark, Summary, Metadata, Timestamp. Jeder Trade ist
  vollständig nachvollziehbar.
- **Config:** Parameter aus `knowledge/backtest_rules.toml`; Konto-/Risikowerte
  ausschließlich aus `config/settings.toml`. **Validierung:** Zeitraum, Daten,
  leere Historie, Preise, Kennzahlen.
- **Tests:** 868 gesamt (155 neue).

### Paper Trading Framework (Sprint 11)

- **Rein bewertend:** die bestehende Pipeline erzeugt täglich Empfehlungen; ein
  **simuliertes** Portfolio eröffnet/bewertet/schließt daraus Positionen.
  **Niemals** echte Orders, **keine** Broker-API, **keine** neue Handelsregel,
  **keine** Änderung an Pipeline oder Backtesting.
- **Subsystem `paper_trading/`:** `paper_runner` (tagweise, **kein** Look-Ahead),
  `portfolio` (Validierung, Kapital/Drawdown/Exposure), `position`
  (Mark-to-Market, Stop/Take-Profit, Trailing Stop **vorbereitet**), `order`
  (OPEN/CLOSE/CANCEL/EXPIRE), `trade`, `journal`, `statistics`, `performance`,
  `base` + zwei Modelle.
- **Engine-Anbindung:** `PaperTradingEngine` (Input `MarketResult`/DataFrame →
  `PaperTradingReport`), `PaperTradingRegistry` (einzige Erweiterungsstelle),
  `PaperTradingCache` (FIFO), Re-Export `paper_trading_result`.
- **PaperTradingResult:** ID, Recommendation-ID, Direction, Recommendation
  Strength, Entry/Current/Exit, Position Size, (Fractional) Shares, Status
  (OPEN/CLOSED/CANCELLED), Entry/Exit Time, PnL €/%, Running/Max Drawdown,
  Current Equity, Portfolio Exposure, Reasons, Warnings, Metadata, Timestamp.
- **Config:** Parameter aus `knowledge/paper_trading_rules.toml`; Konto-/Risiko-
  werte ausschließlich aus `config/settings.toml`. **Validierung:** doppelte
  Position, Größen, Preise, Zeitstempel, Statuswechsel.
- **Tests:** 1045 gesamt (177 neue).

## Was ist bewusst NICHT vorhanden

- Keine Dashboard-Logik, keine Broker-API, keine automatische Orderausführung,
  **keine echten Orders**.
- Backtesting und Paper Trading **simulieren** ausschließlich; sie eröffnen
  keine echte Position und senden keine Order. Die Recommendation Engine liefert
  ausschließlich `RecommendationResult`.

Diese Teile folgen in späteren Sprints (siehe `ROADMAP.md`).

## Qualitätsnachweis (Sprint 11)

| Prüfung | Ergebnis |
|---|---|
| pytest | 1045 Tests bestanden |
| Ruff / Black | konform |
| Import-Zyklen | 0 |
| Entities-Schicht `models/` | 0 Verstöße |
| Plugin-Unabhängigkeit | 0 Verstöße |
| SOLID-Heuristik | 0 Verstöße |
| Pipeline-Konsistenz | 0 Verstöße |
| Ergebnisobjekte unveränderlich (`frozen`) | vollständig |

## Nächster Schritt

Warten auf Freigabe für den nächsten Sprint. Priorisiert: **Kalibrierung** an
realen Daten (Schwellen/Gewichte der Empfehlung, Annualisierung der vorbereiteten
Backtest-Kennzahlen, Aktivierung des vorbereiteten Trailing Stops) sowie
perspektivisch **Dashboard** – weiterhin ohne automatische Orderausführung und
ohne Broker-API.
