# Pipeline – der vollständige Datenfluss von AlphaAI

**Stand:** 2026-07-09 (Sprint 9.5). Dieses Dokument beschreibt die vollständige
End-to-End-Entscheidungskette. Sie enthält **keine** Orderausführung und **keine**
Broker-Anbindung – am Ende steht ausschließlich eine erklärbare Empfehlung.

## Überblick

```
MarketData (OHLCV)
      │
      ▼
IndicatorEngine ── IndicatorResult ─────────────┐
      │                                          │
      ▼                                          │
PatternEngine ──── PatternReport ───────────────┤
      │                                          │
      ▼                                          │
StrategyEngine ─── StrategyReport               │  (Indikatoren/Muster sind
      │                    │                     │   gemeinsame Vorstufen und
      ▼                    │                     │   werden mehrfach genutzt)
ScoreEngine ────── ScoreReport ◄────────────────┘
      │                    │
      ▼                    │
RiskEngine ─────── RiskReport ◄── (Indikatoren, Rohdaten, settings.toml)
      │                    │
      ▼                    │
RecommendationEngine ── RecommendationReport ◄── (Strategy + Score + Risk)
```

Der :class:`pipeline.runner.IntegrationRunner` verdrahtet diese Engines. Jede
Engine erhält ausschließlich Ausgaben vorgelagerter Stufen; keine Engine umgeht
eine Schicht. Indikatoren und Muster sind gemeinsame Vorstufen (Fan-out), keine
Umgehung.

## Stufen im Detail

| # | Stufe | Eingang | Ausgang | Kernaufgabe |
|---|-------|---------|---------|-------------|
| 1 | **Data Layer** | Provider/Universum | `MarketResult` (OHLCV) | Marktdaten beschaffen, normalisieren, validieren |
| 2 | **IndicatorEngine** | OHLCV | `IndicatorResult` | 11 technische Indikatoren (EMA, RSI, ATR, …) |
| 3 | **PatternEngine** | OHLCV (+ Indikatoren) | `PatternReport` | Chartmuster (FVG, BOS/CHoCH, Struktur, …) |
| 4 | **StrategyEngine** | Indikatoren + Muster (+ OHLCV) | `StrategyReport` | objektive Hypothesen (Richtung, Stärke, Vertrauen) |
| 5 | **ScoreEngine** | Strategie + Indikatoren + Muster | `ScoreReport` | objektive Scores über 8 Komponenten |
| 6 | **RiskEngine** | Score + Indikatoren + OHLCV + `settings.toml` | `RiskReport` | 10 Risikokomponenten + Positionsgröße |
| 7 | **RecommendationEngine** | Strategie + Score + Risiko | `RecommendationReport` | Empfehlung über 6 Faktoren + No-Trade-Gates |

Das Gesamtergebnis eines Durchlaufs ist ein unveränderliches
:class:`models.pipeline.PipelineResult`, das die Ausgaben **aller** Stufen bündelt.

## Verkettung im IntegrationRunner

```python
indicators      = indicator_engine.calculate(frame, symbol, timeframe)
patterns        = pattern_engine.detect(frame, symbol, timeframe, indicators=indicators)
strategies      = strategy_engine.evaluate(indicators, patterns, frame, symbol, timeframe)
scores          = score_engine.score(strategies, indicators, patterns, symbol, timeframe)
risks           = risk_engine.assess(scores, indicators, frame, symbol, timeframe, open_positions)
recommendations = recommendation_engine.recommend(strategies, scores, risks, symbol, timeframe)
```

Einstieg:

```python
from pipeline.runner import IntegrationRunner
runner = IntegrationRunner.from_config()          # baut alle 6 Engines aus der Config
result = runner.run(market_result, symbol="AAPL") # ein vollständiger Durchlauf
best   = result.best()                            # höchstbewertete Empfehlung (nur Anzeige)
```

`run_frame(data, symbol)` verpackt einen rohen OHLCV-DataFrame in ein
`MarketResult` und startet die Kette exakt bei der Data Layer (für Tests/Analyse
ohne Netzwerk). `run_all(market_result)` verarbeitet alle Symbole.

## Zuordnung je Hypothese

Über die gesamte Kette bleibt jede Hypothese über ihre `hypothesis_id`
identifizierbar; die Ergebnis-IDs referenzieren einander eindeutig:

```
StrategyResult.hypothesis_id
   └─ ScoreResult.hypothesis_id  (score_id)
        └─ RiskResult.hypothesis_id  (risk_id, score_id)
             └─ RecommendationResult.hypothesis_id  (recommendation_id, risk_id, score_id)
```

`pipeline.consistency.verify_pipeline(result)` prüft diese Referenzen
automatisch: jede Empfehlung besitzt genau einen RiskResult, jeder RiskResult
genau einen ScoreResult, jeder ScoreResult genau einen StrategyResult; alle IDs
sind eindeutig und alle Referenzen gültig.

## Fehlende Daten

Fehlt der Frame eines Symbols, liefert der Runner ein leeres, aber vollständig
**konsistentes** `PipelineResult` (alle Stufen `valid=False`, keine
Empfehlungen, eine Warnung). Die Kette bricht nie unkontrolliert ab.

## Grenzen (bewusst)

Die Pipeline endet mit einer erklärbaren Empfehlung. Es gibt **keine**
Dashboard-Komponente, **keine** Broker-API, **keine** automatische
Orderausführung und **kein** Paper Trading.
