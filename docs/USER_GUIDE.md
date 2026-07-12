# AlphaAI – Benutzerhandbuch (Android)

AlphaAI analysiert Märkte automatisch und zeigt dir jederzeit die aktuell besten
Chancen. **AlphaAI handelt niemals selbst.** Alle Kauf- und Verkaufsentscheidungen
triffst ausschließlich du. Die App zeigt nur Informationen an – es gibt keine
Kauf-/Verkaufsknöpfe.

## Einmalig einrichten

1. Backend starten (siehe `docs/PRODUCTION.md`), z. B. lokal auf deinem Rechner.
2. App öffnen → **Einstellungen** → **Backend-Adresse** eintragen
   (z. B. `http://10.0.2.2:8000/` im Emulator oder die IP deines Rechners im
   WLAN) → **Speichern**.
3. Zurück zu **Home** – fertig.

## Der Tagesablauf

**07:45 – App öffnen.** Die Startseite zeigt sofort den Marktstatus (Europa/USA),
offene Börsen mit Countdown, den letzten und nächsten Scan sowie die Top-Chancen.
Du siehst die europäischen Chancen des Morgens auf einen Blick.

**15:30 – US-Markt öffnet.** App öffnen: die Marktuhr zeigt die eröffnende
US-Session, und die Top-Chancen aktualisieren sich automatisch. Neue Chancen und
neue Risiken werden hervorgehoben.

**22:10 – Tag beendet.** Öffne **Verlauf**, um die Tagesübersicht zu sehen: die
letzten Scans mit Zeitpunkt und den jeweiligen Top-Chancen.

Innerhalb weniger Sekunden hast du alle relevanten Informationen.

## Die Bereiche

- **Home:** Marktstatus, letzter/nächster Scan, Top-Chancen, neue Chancen/Risiken,
  Systemzustand.
- **Chancen:** alle Chancen mit Suche, Filter (Long/Short) und Sortierung
  (Score, Confidence, Risk, Rang). Tippe eine Chance an für Details.
- **Detailseite:** vollständige, unveränderte Analyse einer Aktie – Summary,
  Begründungen, Warnungen, Richtung, Stärke, Score, Confidence, Risk, Muster,
  Strategien, Analytics, Backtest, Paper Trading und Analysezeitpunkt.
- **Märkte:** Zustand von Europa und USA, aktive Session und der Discovery-Status.
- **Verlauf:** die letzten Scans mit Zeitpunkt und Top-Chancen.
- **Einstellungen:** Backend-Adresse, Auto-Refresh, Dark Theme, Hintergrund-
  Refresh, Cache und Debug-Informationen.

## Aktualisieren

- Die App aktualisiert beim Start und beim Zurückkehren automatisch.
- Zum manuellen Aktualisieren nach unten ziehen (Pull-to-Refresh).

## Ohne Verbindung (Offline)

Wenn keine Verbindung zum Backend besteht, zeigt die App den **zuletzt
erfolgreich geladenen Scan** an und weist oben deutlich darauf hin, dass es sich
um einen gespeicherten Stand handelt (inklusive Zeitpunkt).

## Wichtiger Hinweis

AlphaAI ist ein **Analyse- und Entscheidungswerkzeug**, kein Broker. Es führt
keine Orders aus. Die Verantwortung für jede Kauf-/Verkaufsentscheidung liegt
allein bei dir.
