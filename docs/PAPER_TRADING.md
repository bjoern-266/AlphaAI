# Paper Trading (Simuliertes Portfolio unter Live-Bedingungen)

_Wird laufend gepflegt._ Diese Datei beschreibt das Paper-Trading-Framework aus
Sprint 11. Es **bewertet ausschließlich**, wie sich die **bestehenden**
AlphaAI-Empfehlungen unter (simulierten) Live-Marktbedingungen mit einem
**simulierten** Portfolio entwickeln. Es werden **niemals** echte Orders
ausgeführt, es gibt **keine** Broker-API, **keine** neue Handelsregel und
**keine** Änderung an der bestehenden Analysepipeline oder am Backtesting.

## Idee in einem Satz

Die bestehende Pipeline erzeugt täglich Empfehlungen; ein simuliertes Portfolio
eröffnet, bewertet und schließt daraus Positionen und misst objektiv Kapital,
Drawdown, Exposure und Handelsstatistik.

## Kette

```
Live-Marktdaten
      ↓
MarketDataEngine → Indicator → Pattern → Strategy → Score → Risk → Recommendation
      ↓                              (bestehende Pipeline, unverändert)
PaperTradingEngine
      ↓
PaperPortfolio (simuliert)
      ↓
PaperTradingReport (je Position ein PaperTradingResult)
```

## Bausteine

Paket `paper_trading/` (Subsystem, wie `pipeline/`/`backtesting/` – nur der
Zyklenprüfung unterworfen, keine Plugin-Unabhängigkeitsprüfung):

| Modul | Aufgabe |
|---|---|
| `paper_runner.py` | Tägliche Simulation über die bestehende Pipeline (kein Look-Ahead). |
| `portfolio.py` | Das simulierte Portfolio (offene/geschlossene Positionen, Kapital, Drawdown, Exposure, Validierung). |
| `position.py` | Positions-Management: Eröffnen, Mark-to-Market, Stop/Take-Profit, Schließen, Trailing Stop (vorbereitet). |
| `order.py` | Order-Management (OPEN/CLOSE/CANCEL/EXPIRE) und Statuswechsel-Validierung. |
| `trade.py` | Abgeschlossene Trades aus geschlossenen Positionen. |
| `journal.py` | Automatisches Journal (jede Eröffnung/Schließung). |
| `statistics.py` | Handelsstatistik (Win Rate, Profit Factor, …). |
| `performance.py` | Kapital-/Drawdown-/Exposure-Kennzahlen. |
| `base.py` | Schnittstelle `BasePaperTradingModel` der Registry-Modelle. |
| `statistics_model.py`, `performance_model.py` | Die zwei Standard-Registry-Modelle. |

Engine-Anbindung (`engines/`): `paper_trading_engine.py` (Orchestrierung),
`paper_trading_registry.py` (einzige Erweiterungsstelle), `paper_trading_cache.py`
(FIFO-Cache), `paper_trading_result.py` (Re-Export der Ergebnistypen aus
`models.paper_trading`).

## Täglicher Ablauf (paper_runner)

Für jeden Handelstag `i` (ab `warmup_bars`):

1. **Mark-to-Market & Ausstieg.** Alle offenen Positionen werden zum Tageskurs
   bewertet; bei Stop oder Take-Profit werden sie geschlossen (Stop hat bei
   gleichzeitigem Treffer Vorrang).
2. **Verfall (Expire).** Positionen, deren Haltedauer `max_holding_days`
   erreicht, werden geschlossen.
3. **Neue Empfehlung.** Die bestehende Pipeline wird auf den Daten **bis
   einschließlich** Tag `i` ausgewertet (kein Blick in die Zukunft). Ist die
   Empfehlung actionable (Richtung ≠ NEUTRAL, Handlung `OPEN`), wird – sofern
   keine doppelte Position derselben Empfehlung offen ist und `max_open_positions`
   nicht erreicht ist – eine neue Position eröffnet.

Einstieg = Tagesschlusskurs; Stop-/Take-Profit-Abstände, Stückzahl und Kosten
stammen aus der bestehenden Risk Engine.

## PaperTradingResult (Inhalt)

Paper-Trading-ID, Recommendation-ID, Direction, Recommendation Strength, Entry
Price, Current Price, Exit Price, Position Size, (Fractional) Shares, Status
(OPEN/CLOSED/CANCELLED), Entry/Exit Time, PnL €, PnL %, Running Drawdown,
Maximum Drawdown, Current Equity, Portfolio Exposure, Close Reason, Reasons,
Warnings, Metadata, Timestamp.

## Position, Order, Journal

- **Position** kennt Entry, Stop, Take-Profit, Trailing Stop (**vorbereitet**),
  Risiko und die Empfehlung (Direction, Strength, Reasons, Warnings). Positionen
  sind unveränderlich und werden über `dataclasses.replace` fortgeschrieben.
- **Order-Management** unterstützt `OPEN`, `CLOSE`, `CANCEL`, `EXPIRE`. Zulässig
  sind nur Übergänge einer **offenen** Position; eine geschlossene/stornierte
  Position ist endgültig.
- **Journal**: jeder simulierte Trade wird automatisch beim Eröffnen und
  Schließen dokumentiert (Entry, Exit, Grund, PnL, Recommendation, Direction,
  Strength, Reasons, Warnings).

## Statistik & Performance

- **Statistik:** Win Rate, Loss Rate, Profit Factor, Average Winner, Average
  Loser, Average Holding Time (Tage), Current Equity, Portfolio Return, Open/
  Closed Positions.
- **Performance:** Startkapital, aktuelles Kapital, Rendite, laufender und
  maximaler Drawdown, Exposure, realisierte/unrealisierte Ergebnisse,
  Kapitalkurve.

## Validierung

Das Portfolio wirft `PaperTradingValidationError` bei: doppelter Position
derselben Empfehlung, negativer Positionsgröße, ungültigen Preisen, ungültigen
Zeitstempeln und ungültigen Statuswechseln. Die Engine prüft zusätzlich die
Eingabedaten (leere Historie, fehlende Spalten, ungültige Preise, nicht
aufsteigender Zeitindex).

## Simulation & Risiko

- **Keine** echten Orders, **keine** Broker-API – ausschließlich rechnerisch.
- **Fractional Shares** werden vollständig unterstützt (bei
  `account.fractional_shares = false` wird auf ganze Stücke abgerundet).
- **Alle Konto-/Risikoeinstellungen** (Depot, Fractional Shares, Risiko je Trade,
  max. Positionen) stammen ausschließlich aus `config/settings.toml` (über die
  bestehende Risk Engine) – **nicht** aus den Paper-Trading-Regeln.

## Konfiguration

Alle Parameter ausschließlich aus `knowledge/paper_trading_rules.toml`
(keine Hardcodes):

- `[runner]` – `warmup_bars`, `step`, `max_holding_days`, `trailing_distance`
  (**vorbereitet**, 0 = inaktiv).
- `[statistics_model]`, `[performance_model]` – Registry-Modelle.

## Nutzung

```python
from engines.paper_trading_engine import PaperTradingEngine

engine = PaperTradingEngine.from_config()

# Ein Symbol als OHLCV-DataFrame:
report = engine.run_frame(ohlcv_df, symbol="AAPL")
print(report.statistics.win_rate, report.performance.current_equity)
for result in report.results:      # vollständig nachvollziehbar
    print(result.status, result.direction, result.recommendation_strength, result.pnl)

# Mehrere Symbole in einem gemeinsamen Depot:
report = engine.run(market_result)
```

## Neues Paper-Trading-Modell hinzufügen (einziger erlaubter Weg)

1. Datei in `paper_trading/` anlegen, `BasePaperTradingModel` implementieren
   (`compute`), nur `context`/`params` nutzen.
2. In `engines/paper_trading_registry.py::build_default_registry` registrieren.
3. Abschnitt/Parameter in `knowledge/paper_trading_rules.toml` ergänzen. Die
   Engine muss dafür **nicht** geändert werden.
4. Eigene Testdatei `tests/test_paper_<name>.py` anlegen.

## Vorbereitet

Der **Trailing Stop** ist implementiert (`position.apply_trailing_stop`), aber
standardmäßig inaktiv (`trailing_distance = 0.0`). Er kann später ohne
Engine-Änderung über die Regeln aktiviert werden.
