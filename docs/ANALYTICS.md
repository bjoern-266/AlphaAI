# Analytics (Trading Intelligence & Analytics)

_Wird laufend gepflegt._ Diese Datei beschreibt das Analytics-Framework aus
Sprint 12. Es **analysiert ausschließlich** bereits vorhandene Daten aus
Backtesting und Paper Trading und erzeugt daraus **objektive, reproduzierbare
Kennzahlen**. Es **bewertet keine** Trades, trifft **keine**
Handelsentscheidung, verändert **keine** bestehenden Ergebnisse, erzeugt
**keine** neuen Empfehlungen und enthält **keine** Machine-Learning-Komponenten.

## Idee in einem Satz

AlphaAI beginnt, seine eigenen Entscheidungen automatisch auszuwerten: aus den
vorhandenen Backtest-/Paper-Trading-Ergebnissen entstehen transparente
Statistiken – aufgeschlüsselt nach Richtung, Strategie, Risiko, Empfehlungs-
stärke, Zeit und Markt.

## Kette

```
BacktestReport + PaperTradingReport
        ↓
AnalyticsEngine   (normalisiert Trades → führt Registry-Modelle aus)
        ↓
AnalyticsReport (mit AnalyticsResult)
```

Die Engine **liest** die bestehenden Reports; sie schreibt nichts zurück und
ändert keine Engine, kein Backtesting und kein Paper Trading.

## Bausteine

Paket `analytics/` (Subsystem, wie `pipeline/`/`backtesting/`/`paper_trading/` –
nur der Zyklenprüfung unterworfen):

| Modul | Aufgabe |
|---|---|
| `aggregation.py` | Reine Kennzahl-Bausteine (Win Rate, Profit Factor, Expectancy, Drawdown, Gruppierung). Einzige Quelle der Definitionen. |
| `labeling.py` | Ableitung von Strategie (aus `recommendation_id`), Risiko-Level und Score (aus `reasons`) sowie Bucket-Helfer – deterministisch, reproduzierbar. |
| `normalization.py` | Überführt Backtest- und Paper-Trading-Trades in den einheitlichen `AnalyticsTrade` (nur Lesen). |
| `trade_statistics.py` | Gesamt-Kennzahlen + LONG/SHORT. |
| `performance_analyzer.py` | Kapitalkurve, Rendite, Drawdown. |
| `pattern_analysis.py` | Kennzahlen je Pattern. |
| `strategy_analysis.py` | Kennzahlen je Strategie. |
| `recommendation_analysis.py` | Kennzahlen je Recommendation Strength. |
| `risk_analysis.py` | Kennzahlen je Risiko-Level. |
| `market_analysis.py` | Kennzahlen je Marktphase/Volatilität/Liquidität. |
| `time_analysis.py` | Wochentag, Monat, Handelsstunde, Haltedauer. |
| `journal_analysis.py` | Kennzahlen aus dem Paper-Trading-Journal (nur Lesen). |
| `summary_analysis.py` | Menschenlesbare Zusammenfassung. |
| `base.py` | Schnittstelle `BaseAnalyticsModel` der Registry-Plugins. |

Engine-Anbindung (`engines/`): `analytics_engine.py` (Orchestrierung),
`analytics_registry.py` (einzige Erweiterungsstelle), `analytics_cache.py`
(FIFO-Cache), `analytics_result.py` (Re-Export der Ergebnistypen aus
`models.analytics`).

## Normalisierung (AnalyticsTrade)

Backtest- und Paper-Trading-Trades werden in einen einheitlichen
`AnalyticsTrade` überführt. Die Analyse-**Dimensionen** stammen ausschließlich
aus den vorhandenen Daten und sind damit vollständig nachvollziehbar:

- **direction**, **recommendation_strength**, **pnl/pnl_pct**, **holding_time**,
  **entry/exit_time**, **close_reason** – direkt aus dem Quell-Trade,
- **strategy** – aus der `recommendation_id`
  (`rec:score:{strategie}:{richtung}:…`),
- **risk_level** – aus den `reasons` (`Risk LOW/MEDIUM/HIGH`),
- **score** – aus den `reasons` (`Score N/100`),
- **labels** (`pattern`, `market_phase`, `volatility`, `liquidity`) – aus der
  Trade-Metadata, sofern vorhanden.

Fehlt eine Information, wird das Label ``"unbekannt"`` bzw. der Wert ``None``
gesetzt – es werden **keine** Daten erfunden. Pattern-/Markt-Dimensionen sind so
**erweiterbar**: sobald künftige Trades entsprechende Labels tragen, werden sie
automatisch ausgewertet, **ohne** dass eine Engine geändert werden muss.

## AnalyticsResult (Inhalt)

Analytics-ID, Backtest-ID, PaperTrading-ID, Trade Count, Win/Loss Rate, Profit
Factor, Expectancy, Average Winner/Loser, Maximum Drawdown, Average Holding
Time, Average Risk Reward, **Long/Short Statistics**, **Strategy Statistics**,
**Pattern Statistics**, **Recommendation Statistics**, **Risk Statistics**,
**Market Statistics**, **Time Statistics** (Wochentag/Monat/Stunde/Haltedauer),
**Journal Statistics**, Performance (Rendite/Drawdown/Equity-Kurve), Summary,
Warnings, Metadata, Timestamp.

Alle Gruppen-Kennzahlen sind `GroupStatistics` (Trades, Win/Loss Rate, Profit
Factor, Ø Gewinn/Verlust, Ø Return, Ø Haltedauer, Max Drawdown, Total PnL).

## Dimensionen & Zeitanalysen

- **Richtung:** LONG / SHORT.
- **Empfehlungsstärke:** VERY_HIGH … REJECT.
- **Risiko-Level:** low / medium / high.
- **Strategie:** je erzeugender Strategie.
- **Pattern / Marktphase / Volatilität / Liquidität:** label-basiert (erweiterbar).
- **Zeit:** Wochentag, Monat, Handelsstunde, Haltedauer-Bereiche.

## Transparenz & Reproduzierbarkeit

- Jede Kennzahl entsteht ausschließlich aus den Bausteinen in `aggregation.py` –
  keine Blackbox, keine verdeckten Parameter.
- Alle abgeleiteten Dimensionen sind aus `recommendation_id`/`reasons`
  nachvollziehbar.
- Gleiche Eingaben ⇒ gleiche Kennzahlen (per Test abgesichert).
- Der Drawdown wird auf einer Kapitalkurve ``base_capital + kumulierter PnL``
  gemessen; ``base_capital`` steht in `analytics_rules.toml`.

## Validierung

Die Engine meldet `valid = False` bzw. Warnungen bei: fehlenden Reports (weder
Backtest noch Paper Trading), fehlenden Trades, nicht registrierten Modellen und
ungültigen Modellparametern. Kennzahl-Sonderfälle (z. B. Profit Factor `inf`
ohne Verluste) sind dokumentiert und zulässig.

## Konfiguration

Alle Parameter ausschließlich aus `knowledge/analytics_rules.toml`
(keine Hardcodes):

- `[analysis]` – `base_capital`, `score_weak_max`, `score_strong_min`,
  `holding_bands`, Label-Schlüssel (`pattern_label_key`, `market_phase_label_key`,
  `volatility_label_key`, `liquidity_label_key`).
- Ein Abschnitt je Modell (`[trade_statistics]`, `[performance_analyzer]`, …).

## Nutzung

```python
from engines.analytics_engine import AnalyticsEngine

engine = AnalyticsEngine.from_config()
report = engine.analyze(backtest_report, paper_trading_report, symbol="AAPL")

result = report.result
print(result.summary)
print(result.win_rate, result.profit_factor, result.expectancy)
for strategy, stats in result.strategy_statistics.items():
    print(strategy, stats.trade_count, stats.win_rate, stats.profit_factor)
```

Es kann auch nur eine Quelle übergeben werden
(`engine.analyze(backtest_report)` oder
`engine.analyze(paper_report=paper_report)`).

## Neues Analysemodell hinzufügen (einziger erlaubter Weg)

1. Datei in `analytics/` anlegen, `BaseAnalyticsModel` implementieren
   (`compute`), nur `context`/`params` nutzen – **unabhängig** von anderen
   Modellen.
2. In `engines/analytics_registry.py::build_default_registry` registrieren.
3. Abschnitt/Parameter in `knowledge/analytics_rules.toml` ergänzen. Die
   **Engine bleibt unverändert** (Open/Closed).
4. Eigene Testdatei `tests/test_analytics_<name>.py` anlegen.

## Vorbereitung für ein Dashboard

Sämtliche Kennzahlen liegen im `AnalyticsResult` fertig berechnet vor
(Gruppen-Statistiken, Zeitreihen, Equity-Kurve, Summary). Ein späteres Dashboard
muss **nur visualisieren** und darf **keine** Geschäftslogik enthalten – es
greift ausschließlich auf die Felder des `AnalyticsResult` zu.
