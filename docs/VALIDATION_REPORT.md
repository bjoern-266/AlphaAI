# Validation Report – End-to-End-Integration (Sprint 9.5)

**Stand:** 2026-07-09 · **Umfang:** Integration und Validierung der bestehenden
Architektur. **Keine** neuen Features, **keine** Engine-Änderung, **keine**
Orderausführung.

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
- **Verteilung der Stufen:** STRONG_BUY 12 · BUY 5 · WATCH 6 · WAIT 0 · AVOID 0
- **Verteilung der Handlungen:** OPEN 17 · MONITOR 6 · WAIT 0 · SKIP 0

| Szenario | #Strategien | #Empf. | beste Stufe | bestes Rating | Risiko |
|---|---:|---:|---|---:|---|
| trend_up | 2 | 2 | strong_buy | 83.9 | low |
| trend_down | 2 | 2 | strong_buy | 83.7 | low |
| sideways | 2 | 2 | watch | 49.2 | low |
| high_volatility | 3 | 3 | buy | 71.1 | low |
| low_volatility | 1 | 1 | watch | 71.4 | low |
| breakout_up | 2 | 2 | strong_buy | 84.3 | low |
| breakout_down | 2 | 2 | strong_buy | 83.0 | low |
| low_liquidity | 2 | 2 | strong_buy | 81.5 | low |
| high_liquidity | 2 | 2 | strong_buy | 83.9 | low |
| gap_heavy | 1 | 1 | watch | 73.1 | low |
| choppy | 2 | 2 | buy | 73.6 | low |
| weak_data_quality | 2 | 2 | watch | 65.9 | low |
| short_history | 0 | 0 | – | – | – |

## 3. Bestätigte Invarianten (automatisch getestet)

Diese Eigenschaften gelten über **alle** Empfehlungen aller Szenarien
(`test_integration_pipeline.py`):

- ✅ **Konsistenz:** jede Empfehlung → genau ein RiskResult → genau ein
  ScoreResult → genau ein StrategyResult; alle IDs eindeutig, alle Referenzen
  gültig (`verify_pipeline` = 0 Verstöße).
- ✅ **Hohes Risiko deckelt:** keine Empfehlung mit Gesamtrisiko > 66 erreicht
  BUY/STRONG_BUY.
- ✅ **Score allein erzeugt nie BUY:** jede BUY/STRONG_BUY-Empfehlung erfüllt
  **zusätzlich** Konsens ≥ 60, Datenqualität ≥ 60 und Risiko ≤ 66.
- ✅ **Struktur:** Stufe ↔ Handlung konsistent; Rating ∈ 0..100, Confidence ∈
  0..1; alle 10 Risikokomponenten vorhanden; jede Empfehlung ist erklärbar
  (Reasons + Summary, keine Blackbox).
- ✅ **Fehlende Daten:** leeres/zu kurzes Ergebnis bleibt konsistent, keine
  Pipeline-Ausnahme; `short_history`/kein-Frame erzeugen keine BUY-Empfehlung.
- ✅ **Liquidität/Volatilität:** niedrige Liquidität erhöht die Liquiditäts-
  komponente ggü. hoher; hohe Volatilität erhöht die Volatilitätskomponente
  ggü. niedriger.

## 4. Auffälligkeiten

Die synthetischen Szenarien sind **idealisiert** (rauscharme Trends). Das
Fundament arbeitet mechanisch korrekt (0 Konsistenzverstöße, alle Gates halten),
zeigt aber auf diesen Daten ein Verhalten, das für **reale** Märkte kalibriert
werden sollte:

1. **STRONG_BUY zu häufig auf idealisierten Daten (12/23).** Rauscharme, klare
   Trends erzeugen hohe Faktoren und niedriges Risiko → häufig STRONG_BUY. Auf
   realen (verrauschten) Daten fielen Konsens, Datenqualität und Rating
   niedriger aus; die Rarität von BUY/STRONG_BUY ist damit **datenabhängig**,
   nicht durch die Logik garantiert.

2. **Richtungs-Semantik der Stufe (wichtig).** Die `RecommendationLevel`
   (BUY/STRONG_BUY) misst die **Konviktion** einer Hypothese, **nicht** deren
   Richtung. Dadurch erhält ein starkes **bärisches** Setup (`trend_down`,
   `breakout_down`) ebenfalls „STRONG_BUY", und `RecommendationResult` führt die
   Richtung nicht explizit. Fachlich ist „BUY" für eine Short-Hypothese
   irreführend.

3. **WAIT/AVOID traten nicht auf.** Auf diesen Szenarien blieb das niedrigste
   Ergebnis WATCH (Rating ~49). Der Mechanismus für WAIT/AVOID ist über die
   Schwellen und Gates vorhanden und unit-getestet (Sprint 9), wurde end-to-end
   hier aber nicht ausgelöst.

4. **Risiko durchweg LOW.** Selbst `high_volatility` und `gap_heavy` blieben in
   Stufe LOW. Die Volatilitäts-/Gap-Schwellen bzw. deren Gewichte im
   Gesamtrisiko sind für diese synthetischen Amplituden zu nachsichtig.

## 5. Verbesserungsvorschläge (für spätere Sprints)

Bewusst **nicht** in Sprint 9.5 umgesetzt (kein neues Feature, keine
Engine-Änderung) – als priorisierte Empfehlungen dokumentiert:

1. **Richtung in die Empfehlung aufnehmen** (höchste Priorität): `direction` in
   `RecommendationResult` führen und die BUY-Familie an bullische Hypothesen
   binden (bzw. eine SELL-/SHORT-Familie oder neutrale „Konviktions"-Benennung
   einführen). Behebt Auffälligkeit 2.
2. **Recommendation-Schwellen/Gewichte an realen Daten kalibrieren**
   (`recommendation_rules.toml`): `buy_min`/`strong_buy_min` anheben oder
   Faktorgewichte anpassen, sodass BUY selten und STRONG_BUY außergewöhnlich
   ist. Behebt Auffälligkeit 1/3.
3. **Risiko-Schwellen schärfen** (`risk_rules.toml`): Volatilitäts-/Gap-
   Grenzen und Gewichte so justieren, dass hohe Volatilität/Gaps zuverlässig
   MEDIUM/HIGH ergeben. Behebt Auffälligkeit 4.
4. **Validierung an echten historischen Daten** (yfinance-Provider) ergänzen,
   sobald Netzwerkzugriff Teil der Testumgebung ist – die synthetischen
   Szenarien dienen bis dahin als deterministische Kalibrier-Basis.

## 6. Fazit

Die **Integration** der sieben Stufen ist vollständig, deterministisch und
**konsistent** (0 Referenz-/Eindeutigkeitsverstöße über 180 Tests). Die
**mechanischen** Entscheidungs-Invarianten (No-Trade-Gates, „Score allein nie
BUY", „hohes Risiko deckelt") sind end-to-end bestätigt. Für den **fachlichen
Feinschliff** – Richtungs-Semantik und Kalibrierung an realen Daten – liegen
klare, priorisierte Verbesserungsvorschläge vor. Das Fundament ist bereit für
diese Kalibrierung; die Architektur selbst bleibt unverändert.
