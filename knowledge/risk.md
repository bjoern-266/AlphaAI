# Risikoregeln

Risikomanagement ist der wichtigste Baustein einer nachhaltigen
Daytrading-Analyse. Diese Regeln beschreiben, wie Alpha AI Risiko bewertet.
Die konkreten Zahlenwerte stehen in `config/settings.toml` und werden hier
nur erläutert.

## Kernprinzipien

1. **Fester Risikoanteil pro Trade.** Pro Empfehlung wird nur ein kleiner,
   fest definierter Anteil des Depots riskiert (`risk.risk_per_trade_pct`).
2. **Begrenzte Anzahl offener Positionen.** Das Gesamtrisiko wird über
   `risk.max_open_positions` begrenzt.
3. **Tagesverlustgrenze.** Ist der maximale Tagesverlust
   (`risk.max_daily_loss_pct`) erreicht, werden keine neuen Empfehlungen mehr
   erzeugt.
4. **Stop zuerst.** Jede Empfehlung enthält einen definierten Stop-Loss,
   bevor ein Kursziel betrachtet wird.

## Positionsgröße (Prinzip)

Die Positionsgröße ergibt sich aus dem erlaubten Risiko und dem Abstand zum
Stop-Loss:

```
Risikobetrag   = Depotgröße * risk_per_trade_pct
Positionsgröße = Risikobetrag / (Einstieg - Stop-Loss)
```

Ob dabei Bruchstücke erlaubt sind, steuert `account.fractional_shares`.

## Hinweis

Diese Regeln sind Analysegrundlage, keine Anlageberatung. Alpha AI führt
keine Orders aus.
