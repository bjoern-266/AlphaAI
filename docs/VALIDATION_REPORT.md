# Validation Report – End-to-End-Integration (Sprint 9.5, Update 9.6/10/11)

**Stand:** 2026-07-10 · **Umfang:** Integration und Validierung der bestehenden
Architektur. **Keine** neuen Features, **keine** neue Engine, **keine**
Orderausführung.

> **➕ Update Sprint 11 – Paper Trading.** Das neue Paper-Trading-Framework
> (`paper_trading/`, `engines/paper_trading_*`) bewertet **rein** die Entwicklung
> der **bestehenden** Empfehlungen mit einem **simulierten** Portfolio; es führt
> **niemals** echte Orders aus und ändert keine Engine. **Offene Punkte:** der
> **Trailing Stop** ist vorbereitet (implementiert, per Default inaktiv über
> `trailing_distance = 0.0`) und an realen Daten zu kalibrieren; ebenso bleibt die
> Schwellen-/Gewichts-Kalibrierung der Empfehlung offen. Diese Schritte ändern
> bewusst Verhalten und sind daher eigene Sprints.

> **➕ Update Sprint 10 – Historical Backtesting.** Das neue Backtesting-Framework
> (`backtesting/`, `engines/backtest_*`) bewertet **rein** die historische
> Entwicklung der **bestehenden** Empfehlungen; es ändert keine Engine und
> erzeugt keine Order. **Offener Kalibrierungspunkt:** die risikoadjustierten
> Kennzahlen **Sharpe/Sortino/Calmar** sind bewusst **vorbereitet** (Formeln
> implementiert, aber nicht annualisiert/kalibriert und `None` bei zu wenig
> Daten). Sie sind an realen historischen Daten und einer belastbaren
> Periodizität zu kalibrieren – ein eigener Schritt, kein Teil von Sprint 10.
> Ebenso bleibt die **Schwellen-/Gewichts-Kalibrierung** der Empfehlung an
> realen Daten offen.

> **✅ Update Sprint 9.6 – Kernbefund behoben.** Der in 9.5 dokumentierte
> Befund *„Strong bearish setup → STRONG_BUY"* ist **vollständig behoben**.
> Richtung und Qualität sind jetzt getrennt: `RecommendationResult` trägt
> `direction` (LONG/SHORT/NEUTRAL) **und** `recommendation_strength`
> (VERY_HIGH/HIGH/MEDIUM/LOW/REJECT). Die Stärke enthält **kein** BUY/SELL/LONG/
> SHORT mehr. Ein bärisches Setup ist nun **SHORT** mit ggf. hoher Stärke –
> niemals „BUY". Die Bewertungslogik ist dabei unverändert (nur Semantik/
> Benennung); die Rating-Werte sind identisch zu 9.5.
>
> Belege (echte Pipeline): `trend_down` → **SHORT / VERY_HIGH**,
> `breakout_down` → **SHORT / VERY_HIGH**, `trend_up` → **LONG / VERY_HIGH**,
> `sideways` → **MEDIUM** bei uneinigen Richtungen. Abgesichert u. a. durch
> `test_bearish_scenarios_are_short_not_buy` und
> `test_strength_never_contains_direction_terms`.

Grundlage: 13 deterministische, echte Marktszenarien (`tests/scenarios.py`), die
durch die **vollständige** Pipeline (`IntegrationRunner`) laufen, plus 180
Integrations-Tests (`tests/test_integration_pipeline.py`). Kein Mock.

## 1. Getestete Szenarien

| Szenario | Beschreibung | Abgedeckte Anforderung |
|---|---|---|
| `trend_up` | stetiger Aufwärtstrend | Trendmarkt |
| `trend_down` | stetiger Abwärtstrend | Bärischer Trend |
| `sideways` | Oszillation um ein Niveau | Seitwärtsmarkt |
| `high_volatility` | große Zufallsschwankungen | Hohe Volatilität |
| `low_volatility` | ruhiger Drift | Niedrige Volatilität |
| `breakout_up` | Seitwärts → Ausbruch nach oben | Bullischer Ausbruch |
| `breakout_down` | Seitwärts → Ausbruch nach unten | Bärischer Ausbruch |
| `low_liquidity` | Trend, winziges Volumen | Niedrige Liquidität |
| `high_liquidity` | Trend, sehr großes Volumen | Hohe Liquidität |
| `gap_heavy` | viele Overnight-Gaps | Gap-Risiko |
| `choppy` | richtungsloser Random-Walk | Strategie-Konflikt (potenziell) |
| `weak_data_quality` | NaN-Lücken in Schlusskursen | Schwache Datenqualität |
| `short_history` | 20 Kerzen | Fehlende/zu wenig Daten |
| _(kein Frame)_ | leeres `MarketResult` | Fehlende Daten |

Zusätzlich geprüft (über alle Szenarien): mehrere bestätigende Strategien, hoher
Score + niedriges Risiko, hoher Score ohne Konsens.

## 2. Ergebnisse (Statistik)

Battery über die 13 Frame-Szenarien:

- **Empfehlungen gesamt:** 23
- **Konsistenz-Verstöße:** **0** (alle Referenzen eindeutig und gültig)
- **Verteilung der Richtung (9.6):** LONG 12 · SHORT 11 · NEUTRAL 0
- **Verteilung der Stärke (9.6):** VERY_HIGH 12 · HIGH 5 · MEDIUM 6 · LOW 0 · REJECT 0
- Rating-Werte **unverändert** ggü. 9.5 (nur Benennung Richtung/Stärke geändert).

| Szenario | #Empf. | beste Richtung | beste Stärke | bestes Rating |
|---|---:|---|---|---:|
| trend_up | 2 | LONG | very_high | 83.9 |
| trend_down | 2 | SHORT | very_high | 83.7 |
| sideways | 2 | SHORT | medium | 49.2 |
| high_volatility | 3 | SHORT | high | 71.1 |
| low_volatility | 1 | LONG | medium | 71.4 |
| breakout_up | 2 | LONG | very_high | 84.3 |
| breakout_down | 2 | SHORT | very_high | 83.0 |
| low_liquidity | 2 | LONG | very_high | 81.5 |
| high_liquidity | 2 | LONG | very_high | 83.9 |
| gap_heavy | 1 | LONG | medium | 73.1 |
| choppy | 2 | SHORT | high | 73.6 |
| weak_data_quality | 2 | LONG | medium | 65.9 |
| short_history | 0 | – | – | – |

## 3. Bestätigte Invarianten (automatisch getestet)

Diese Eigenschaften gelten über **alle** Empfehlungen aller Szenarien
(`test_integration_pipeline.py`):

- ✅ **Konsistenz:** jede Empfehlung → genau ein RiskResult → genau ein
  ScoreResult → genau ein StrategyResult; alle IDs eindeutig, alle Referenzen
  gültig (`verify_pipeline` = 0 Verstöße).
- ✅ **Hohes Risiko deckelt:** keine Empfehlung mit Gesamtrisiko > 66 erreicht
  hohe Stärke (HIGH/VERY_HIGH).
- ✅ **Score allein erzeugt nie hohe Stärke:** jede HIGH/VERY_HIGH-Empfehlung
  erfüllt **zusätzlich** Konsens ≥ 60, Datenqualität ≥ 60 und Risiko ≤ 66.
- ✅ **Richtung ↔ Stärke getrennt (9.6):** jede Richtung folgt der Strategie
  (LONG/SHORT/NEUTRAL); die Stärke enthält nie BUY/SELL/LONG/SHORT. Ein
  bärisches Setup ist SHORT, nie „BUY".
- ✅ **Struktur:** Stärke ↔ Handlung konsistent; Rating ∈ 0..100, Confidence ∈
  0..1; alle 10 Risikokomponenten vorhanden; jede Empfehlung ist erklärbar
  (Reasons + Summary, keine Blackbox).
- ✅ **Fehlende Daten:** leeres/zu kurzes Ergebnis bleibt konsistent, keine
  Pipeline-Ausnahme; `short_history`/kein-Frame erzeugen keine hohe Stärke.
- ✅ **Liquidität/Volatilität:** niedrige Liquidität erhöht die Liquiditäts-
  komponente ggü. hoher; hohe Volatilität erhöht die Volatilitätskomponente
  ggü. niedriger.

## 4. Auffälligkeiten

Die synthetischen Szenarien sind **idealisiert** (rauscharme Trends). Das
Fundament arbeitet mechanisch korrekt (0 Konsistenzverstöße, alle Gates halten),
zeigt aber auf diesen Daten ein Verhalten, das für **reale** Märkte kalibriert
werden sollte:

1. **VERY_HIGH zu häufig auf idealisierten Daten (12/23).** Rauscharme, klare
   Trends erzeugen hohe Faktoren und niedriges Risiko → häufig VERY_HIGH. Auf
   realen (verrauschten) Daten fielen Konsens, Datenqualität und Rating
   niedriger aus; die Rarität hoher Stärke ist damit **datenabhängig**, nicht
   durch die Logik garantiert.

2. **Richtungs-Semantik der Stufe.** ✅ **Behoben in Sprint 9.6.** Zuvor maß die
   Empfehlungsstufe (STRONG_BUY/BUY) die Konviktion und implizierte zugleich eine
   Richtung, sodass ein bärisches Setup „STRONG_BUY" erhielt. Nun sind
   `direction` (LONG/SHORT/NEUTRAL) und `recommendation_strength`
   (VERY_HIGH … REJECT) vollständig getrennt; `trend_down`/`breakout_down` sind
   **SHORT / VERY_HIGH**.

3. **LOW/REJECT traten nicht auf.** Auf diesen Szenarien blieb die niedrigste
   Stärke MEDIUM (Rating ~49). Der Mechanismus für LOW/REJECT ist über die
   Schwellen und Gates vorhanden und unit-getestet, wurde end-to-end hier aber
   nicht ausgelöst.

4. **Risiko durchweg LOW.** Selbst `high_volatility` und `gap_heavy` blieben in
   Stufe LOW. Die Volatilitäts-/Gap-Schwellen bzw. deren Gewichte im
   Gesamtrisiko sind für diese synthetischen Amplituden zu nachsichtig.

## 5. Verbesserungsvorschläge

1. **Richtung in die Empfehlung aufnehmen** (höchste Priorität): ✅ **umgesetzt
   in Sprint 9.6.** `RecommendationResult` trägt jetzt `direction`
   (LONG/SHORT/NEUTRAL) getrennt von `recommendation_strength`; die Stärke
   impliziert nie mehr eine Richtung. Behebt Auffälligkeit 2.
2. **Recommendation-Schwellen/Gewichte an realen Daten kalibrieren** (offen,
   `recommendation_rules.toml`): `high_min`/`very_high_min` anheben oder
   Faktorgewichte anpassen, sodass HIGH selten und VERY_HIGH außergewöhnlich
   ist. Adressiert Auffälligkeit 1/3. Bewusst **nicht** in 9.6 (Semantik-Sprint,
   keine geänderten Handelsregeln).
3. **Risiko-Schwellen schärfen** (offen, `risk_rules.toml`): Volatilitäts-/Gap-
   Grenzen und Gewichte so justieren, dass hohe Volatilität/Gaps zuverlässig
   MEDIUM/HIGH ergeben. Adressiert Auffälligkeit 4.
4. **Validierung an echten historischen Daten** (offen, yfinance-Provider)
   ergänzen, sobald Netzwerkzugriff Teil der Testumgebung ist – die
   synthetischen Szenarien dienen bis dahin als deterministische Kalibrier-Basis.

## 6. Fazit

Die **Integration** der sieben Stufen ist vollständig, deterministisch und
**konsistent** (0 Referenz-/Eindeutigkeitsverstöße). Die **mechanischen**
Entscheidungs-Invarianten (No-Trade-Gates, „Score allein nie hohe Stärke",
„hohes Risiko deckelt") sind end-to-end bestätigt. Der zentrale fachliche
Befund aus 9.5 – die vermischte Richtungs-/Stärke-Semantik – ist in **Sprint
9.6** vollständig **behoben**: Richtung (`Direction`) und Qualität
(`RecommendationStrength`) sind sauber getrennt; ein bärisches Setup wird nie
mehr als „BUY" dargestellt. Offen bleibt die **Kalibrierung** an realen Daten
(eigene Folge-Sprints); die Architektur selbst bleibt unverändert.
