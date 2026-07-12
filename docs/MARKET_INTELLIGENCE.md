# Market Intelligence (Chancen-Priorisierung)

_Wird laufend gepflegt._ Diese Datei beschreibt das Market-Intelligence-Framework
aus Sprint 14. Es **bewertet ausschließlich bereits vorhandene Ergebnisse**
(Empfehlung, Risiko, Analytics, Backtesting, Paper Trading) und priorisiert
daraus die objektiv besten Chancen. Es **berechnet keine** neue Handelsregel,
verändert **keine** bestehenden Ergebnisse, trifft **keine** Handelsentscheidung
und enthält **keine** Machine-Learning-Komponenten.

## Idee in einem Satz

AlphaAI analysiert erstmals den gesamten Markt und stellt die relevantesten
Chancen mit vollständiger Begründung und transparenter Herleitung nach oben –
ohne selbst eine neue Bewertung zu erfinden.

## Kette

```
RecommendationReport + AnalyticsReport + BacktestReport + PaperTradingReport
        ↓  je Aktie gebündelt als MarketCandidate
MarketIntelligenceEngine (führt die Bewertungsmodelle je Kandidat aus)
        ↓
Opportunity je Aktie  →  Ranking  →  Statistik / Herleitung / Watchlists
        ↓
OpportunityReport  →  Dashboard (Seite „Market Intelligence")
```

Die Engine **liest** die bestehenden Ergebnisse; sie schreibt nichts zurück und
ändert keine Engine (Recommendation/Risk/Score/Strategy/Pattern/Indicator/
Analytics bleiben unverändert).

## Bausteine

Paket `market_intelligence/` (Subsystem, wie `analytics/` – nur der
Zyklenprüfung unterworfen):

| Modul | Aufgabe |
|---|---|
| `base.py` | Schnittstelle `BaseOpportunityModel` der Registry-Plugins + Helfer (`require_weight`, `clamp_score`). |
| `opportunity.py` | Die fünf Bewertungsmodelle (jedes leitet seinen Beitrag aus **einer** vorhandenen Kennzahl ab) und `build_opportunity` (gewichtete Zusammenfassung → eine `Opportunity`). |
| `ranking.py` | Reine Sortier-/Rang-Bausteine (Sortierkriterien, `assign_ranks`, `top`, Top-Größen). |
| `ranking_engine.py` | Ranking-Zusammenbau (`rank` = Sortierung + Rangvergabe) und `build_watchlists`. |
| `filter.py` | `OpportunityFilter` + Filterfunktionen (Long/Short/Watch, Risiko, Confidence, Stärke, Markt, Branche, Börse). |
| `explainer.py` | Transparente Herleitung je Chance (Faktoren, Risiken, „warum nicht höher"). |
| `statistics.py` | Kennzahlen über alle Chancen (Anzahlen, Durchschnitte, Top-Branchen/Märkte). |
| `cache.py` | `OpportunityCache` (FIFO, Spezialisierung von `core.cache.Cache`). |

Engine-Anbindung (`engines/`): `market_intelligence_engine.py` (Orchestrierung +
Regel-Laden), `market_intelligence_registry.py` (einzige Erweiterungsstelle),
`market_intelligence_cache.py` (Re-Export), `market_intelligence_result.py`
(Re-Export der Ergebnistypen aus `models.opportunity`).

## Der Opportunity Score

**Kein neues Bewertungssystem.** Der Score ist die **gewichtete Zusammenfassung**
von fünf bereits vorhandenen Signalen:

| Komponente | Quelle (unverändert) | Standard-Gewicht |
|---|---|---|
| `recommendation` | `RecommendationResult.overall_rating` (0..100) | 0.40 |
| `risk` | `RecommendationResult.metadata['factors']['risk']` (0..100, höher = geringeres Risiko) | 0.20 |
| `analytics` | `AnalyticsReport.result.win_rate` (0..1) | 0.15 |
| `backtest` | `BacktestReport.results[0].win_rate` (0..1) | 0.15 |
| `paper_trading` | `PaperTradingReport.statistics.win_rate` (0..1) | 0.10 |

Alle Gewichte stehen ausschließlich in `knowledge/market_intelligence_rules.toml`
und ergeben zusammen 1.0. Fehlt eine Quelle, wird ihr Beitrag ausgelassen und
über die verbleibenden Gewichte normalisiert – es wird **nichts** ersatzweise
berechnet. Richtung, Stärke, Confidence, Rating und Risiko werden **unverändert**
aus der Empfehlung übernommen; eine Aktie ohne Empfehlung wird als **Watch**
(neutral, Score 0) geführt.

## Ranking, Filter, Sortierung

- **Ranking:** alle Chancen werden sortiert und mit Rang 1..N versehen. Top-5/10/
  20/50 werden unterstützt.
- **Sortierung:** `opportunity_score` (Standard), `confidence`, `risk`,
  `recommendation` (Stärke), `alphabetical`.
- **Filter:** Long/Short/Watch, minimale Confidence, maximales Risiko, minimale
  Empfehlungsstärke, Markt, Branche, Börse – reine Auswahl, keine Berechnung.

## Explainer (keine Blackbox)

Für jede Chance wird erklärt: die Kernaussage zum Platz, die entscheidenden
Faktoren (stärkste Komponenten), die bestehenden Risiken sowie „warum nicht
höher?" (Vergleich zur nächstbesseren Chance). Alle Angaben stammen aus den
vorhandenen Werten der Chance.

## Watchlists & Statistik

- **Watchlists:** `top` (beste Chancen), `long`, `short` – Reihenfolge = Ranking,
  Größen aus der Regeldatei.
- **Statistik:** Anzahl analysierter Aktien, Long/Short/Watch, Ø Score, Ø Risiko,
  Ø Confidence, Top-Branchen, Top-Märkte.

## Eingaben / Ausgaben

- **Eingabe:** `Sequence[MarketCandidate]` – je Aktie ihr Ticker/Metadaten plus
  die bereits vorhandenen Reports (alle optional).
- **Ausgabe:** ein `OpportunityReport` (priorisierte `Opportunity`-Liste +
  Statistik + Herleitungen + Watchlists). Alle Typen sind unveränderlich
  (`frozen`).

## Dashboard

Neue Seite **Market Intelligence** (additiv über Router/Registry, die
`DashboardEngine` bleibt unverändert): Top Opportunities, vollständiges Ranking
(mit Suche/Filter), Heatmap der Scores, Erklärung und Kennzahlen. Das Dashboard
**visualisiert ausschließlich** den `OpportunityReport` – **keine** Berechnung im
Frontend.

## Validierung

Leere Kandidatenliste (Report ungültig, aber ohne Exception), fehlende/ungültige
Reports (Komponente wird ausgelassen), doppelte Ticker (übersprungen mit
Warnung), fehlende Ticker (übersprungen), ungültige Gewichte (Regel-Ladefehler),
Scores außerhalb 0..100 (begrenzt). Fehler eines einzelnen Modells werden isoliert
als Warnung behandelt.

## Erweitern

- **Neues Bewertungsmodell:** Klasse von `BaseOpportunityModel` ableiten
  (`compute`), in `engines/market_intelligence_registry.py` registrieren, Abschnitt
  mit `weight` in `knowledge/market_intelligence_rules.toml` ergänzen (Gewichte
  müssen weiterhin 1.0 ergeben). Die **Engine bleibt unverändert** (Open/Closed).

## Tests

201 Tests decken Modelle, die fünf Bewertungsmodelle, `build_opportunity`,
Ranking, Filter, Explainer, Statistik, Cache, Registry, das Regel-Laden, die
Engine (inkl. Validierung/Cache/Determinismus), End-to-End-Szenarien und die
Dashboardseite ab.
