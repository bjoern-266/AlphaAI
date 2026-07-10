# Backtesting (Historisches Backtesting-Framework)

_Wird laufend gepflegt._ Diese Datei beschreibt das Backtesting-Framework aus
Sprint 10. Es **bewertet ausschließlich**, wie sich die **bestehenden**
AlphaAI-Empfehlungen historisch entwickelt hätten. Es erzeugt **keine** neue
Handelsregel, ändert **keine** Empfehlung und keine Engine, führt **keine**
echte Order aus (Trades werden ausschließlich rechnerisch simuliert), und es
gibt **kein** Dashboard, **keine** Broker-API und **kein** Paper-Trading.

## Idee in einem Satz

Historische Marktdaten laufen zeitpunktweise durch die **unveränderte**
AlphaAI-Pipeline; die dabei entstehenden Empfehlungen werden als Trades
simuliert und objektiv mit Kennzahlen bewertet.

## Kette

```
Historische Marktdaten
        ↓
MarketDataEngine → IndicatorEngine → PatternEngine → StrategyEngine
        ↓
ScoreEngine → RiskEngine → RecommendationEngine   (bestehende Pipeline)
        ↓
BacktestEngine
        ↓
BacktestReport (je Symbol ein BacktestResult)
```

Die ersten sieben Stufen sind der bestehende
`pipeline.runner.IntegrationRunner`. Das Framework hängt **nur hinten** an –
es greift nicht in die Fachlogik ein.

## Bausteine

Paket `backtesting/` (Subsystem, keine Plugin-Familie mit eigener
Unabhängigkeitsprüfung – analog zu `pipeline/`):

| Modul | Aufgabe |
|---|---|
| `historical_runner.py` | Führt die Pipeline fensterweise über die Historie aus (kein Look-Ahead) und sammelt die Empfehlungen als `HistoricalSignal`. |
| `trade_simulator.py` | Simuliert aus den Signalen Trades (Entry/Exit/Stop/Take-Profit), Fractional Shares, Kosten. Keine echte Order. |
| `performance_metrics.py` | Reine Kennzahlen: Win/Loss Rate, Profit Factor, Ø Gewinn/Verlust, Ø CRV, Ø Haltedauer, Expectancy. |
| `equity_curve.py` | Kapitalkurve und Drawdown (prozentual/absolut). |
| `statistics.py` | Risikoadjustierte Kennzahlen (Sharpe/Sortino/Calmar) – **vorbereitet**. |
| `benchmark.py` | Vergleichsmaßstab **Buy & Hold** als Referenz. |
| `base.py` | Schnittstelle `BaseBacktestModel` + Parameter-Hilfen. |
| `performance_model.py`, `drawdown_model.py`, `ratio_model.py`, `benchmark_model.py` | Die vier Standard-Backtest-Modelle (Registry-Plugins). |

Engines-Anbindung (`engines/`): `backtest_engine.py` (Orchestrierung),
`backtest_registry.py` (einzige Erweiterungsstelle), `backtest_cache.py`
(FIFO-Cache), `backtest_result.py` (Re-Export der Ergebnistypen aus
`models.backtest`).

## Datenfluss im Detail

1. **Historical Runner.** Für jeden Auswertungspunkt `i` (ab `warmup_bars`, in
   Schritten `step`) läuft `frame.iloc[:i+1]` durch die Pipeline. Es werden
   **nur** Kerzen bis einschließlich `i` gesehen – daher kein Blick in die
   Zukunft. Aus der besten Empfehlung und der zugehörigen Risikobewertung
   entsteht ein `HistoricalSignal` (Einstieg = Schlusskurs von `i`, Stop-/
   Take-Profit-Abstand, Stückzahl und Kosten aus der Risk Engine).
2. **Trade-Simulator.** Ein Signal wird nur zum Trade, wenn es *actionable* ist
   (klare Richtung, Handlung `OPEN`, positive Stückzahl und positiver
   Stop-Abstand). Ab der nächsten Kerze wird vorwärts simuliert:
   - **LONG:** Stop bei `entry − stop_distance`, Take-Profit bei
     `entry + take_profit_distance`.
   - **SHORT:** Stop bei `entry + stop_distance`, Take-Profit bei
     `entry − take_profit_distance`.
   - Trifft eine Kerze **beide** Schwellen, wird konservativ der **Stop**
     angenommen.
   - Ohne Treffer folgt nach `max_holding_bars` ein Zeit-Ausstieg (oder am
     Datenende ein `END_OF_DATA`-Ausstieg) zum Schlusskurs.
   - Es ist **nie mehr als eine Position gleichzeitig** offen; Signale während
     einer offenen Position werden übersprungen.
3. **Kennzahlen & Kurve.** Aus den Trades werden Kapitalkurve, Drawdown,
   Kennzahlen und der Benchmark berechnet – über die registrierten Modelle.
4. **BacktestResult.** Die Engine setzt das Ergebnis aus den Modell-Kennzahlen
   zusammen (Fallbacks, falls ein Modell deaktiviert ist).

## BacktestResult (Inhalt)

Backtest ID, Symbol, Timeframe, Start-/Enddatum, Anzahl Signale, Anzahl Trades,
Win Rate, Loss Rate, Profit Factor, Ø Gewinn, Ø Verlust, Ø Chance-Risiko-
Verhältnis, Ø Haltedauer (in Kerzen), Maximaler Drawdown, Expectancy,
Sharpe/Sortino/Calmar (**vorbereitet**, ggf. `None`), Gesamtrendite,
Endkapital, Equity Curve, Trade-Liste, Benchmark, Summary, Reasons, Warnings,
Metadata, Timestamp.

### Transparenz je Trade

Für **jeden** simulierten Trade werden gespeichert: Entry, Exit, Stop,
Take-Profit, Risiko (Betrag), Recommendation-ID, Direction, Recommendation
Strength, Reasons und Warnings – jeder Trade ist damit vollständig
nachvollziehbar.

## Simulation & Risiko

- Es werden **keine** echten Orders ausgeführt; alle Trades sind rechnerisch.
- **Fractional Shares** werden vollständig unterstützt (die Stückzahl kommt aus
  der Positionsgröße der Risk Engine).
- **Alle Konto-/Risikoeinstellungen** (Depot, Fractional Shares, Risiko je
  Trade, max. Positionen) stammen ausschließlich aus `config/settings.toml`
  (über die bestehende Risk Engine) – **nicht** aus den Backtest-Regeln.

## Benchmark

Optionaler Vergleich gegen **Buy & Hold** (Kauf zum ersten, Verkauf zum letzten
Schlusskurs des Zeitraums, gesamtes Startkapital, Fractional Shares). Der
Benchmark ist reine **Referenz** – keine Empfehlung.

## Validierung

`BacktestEngine` prüft vor dem Lauf und meldet `valid = False` mit Warnung bei:
ungültigem Zeitraum (Zeitindex nicht aufsteigend), fehlenden Daten (Spalte
`close` fehlt), leerer Historie, ungültigen Preisen (≤ 0), zu kurzer Historie.
Nach dem Lauf werden **ungültige Kennzahlen** erkannt (nicht-endliche Werte –
außer dem zulässigen `inf`-Sonderfall des Profit Factors ohne Verluste – sowie
Win Rate außerhalb 0..1 oder Drawdown außerhalb 0..100 %).

## Konfiguration

Alle Parameter ausschließlich aus `knowledge/backtest_rules.toml`
(keine Hardcodes):

- `[engine]` – `warmup_bars`, `step`, `min_history_bars` (Historical Runner).
- `[simulation]` – `max_holding_bars`, `apply_costs`, `breakeven_epsilon`.
- `[performance_model]`, `[drawdown_model]`, `[ratio_model]`
  (`risk_free_rate`, `periods_per_year`), `[benchmark_model]`.

## Nutzung

```python
from engines.backtest_engine import BacktestEngine
from repositories.repository_factory import build_repository  # o. eigener Loader

engine = BacktestEngine.from_config()

# Ein Symbol als OHLCV-DataFrame:
result = engine.run_frame(ohlcv_df, symbol="AAPL", timeframe="base")
print(result.summary)
for trade in result.trades:      # vollständig nachvollziehbar
    print(trade.direction, trade.recommendation_strength, trade.profit)

# Mehrere Symbole als MarketResult:
report = engine.run(market_result)     # BacktestReport
best = report.best(1)                  # reine Anzeige, keine Handelsentscheidung
```

## Neues Backtest-Modell hinzufügen (einziger erlaubter Weg)

1. Datei in `backtesting/` anlegen, `BaseBacktestModel` implementieren
   (`compute`), nur `context`/`params` nutzen.
2. In `engines/backtest_registry.py::build_default_registry` registrieren.
3. Abschnitt/Parameter in `knowledge/backtest_rules.toml` ergänzen. Die Engine
   muss dafür **nicht** geändert werden.
4. Eigene Testdatei `tests/test_backtest_<name>.py` anlegen.

## Vorbereitete Kennzahlen

Sharpe-, Sortino- und Calmar-Ratio sind mit Standardformeln implementiert, aber
bewusst **vorbereitet**: nicht annualisiert/kalibriert (bis eine belastbare
Periodizität und ein realer Datensatz feststehen) und `None` bei zu wenig Daten.
Kalibrierung ist im `VALIDATION_REPORT.md` als offener fachlicher Schritt
festgehalten.
