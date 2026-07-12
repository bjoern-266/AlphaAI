# Live Operations (Live Market Operations Platform)

_Wird laufend gepflegt._ Diese Datei beschreibt die Live Market Operations
Platform aus Sprint 16. Ab diesem Sprint arbeitet AlphaAI als **produktives
tägliches Analyse-System**: der Benutzer startet AlphaAI, danach übernimmt das
System sämtliche Marktanalysen automatisch – ohne manuelle Discovery- oder
Scanner-Läufe. **Alle Kauf-/Verkaufsentscheidungen trifft ausschließlich der
Benutzer.** Es werden **niemals** Orders ausgeführt.

## Idee in einem Satz

AlphaAI erkennt automatisch die Marktzeiten, plant und startet die Analyse-Jobs
selbst und zeigt jederzeit den aktuellen Marktstatus und die besten Chancen – der
Benutzer erhält ohne Eingaben eine belastbare Entscheidungsgrundlage.

## Kette

```
Marktuhr (Zeit/Zeitzonen/DST)     Zeitplan (Jobs je Uhrzeit)
              \                     /
        Operations Engine  (Taktgeber: tick())
              |   startet fällige Jobs (INJIZIERT), seriell, ein Discovery zugleich
        Bestehende Pipeline (Market Discovery / Analytics / Market Intelligence)
              |
        OperationReport  (UI-unabhängig)
              |
        Dashboard „Live Operations"  ·  spätere REST-API  ·  spätere Mobile-Apps
```

Die Operations Engine **berechnet nichts** und **importiert nichts** aus der
Pipeline: die eigentlichen Jobs (Discovery etc.) und die Uhr werden **injiziert**.
So bleibt das Subsystem entkoppelt (nur `models`/`core`), es entsteht kein
Import-Zyklus und keine bestehende Engine wird verändert.

## Bausteine

Paket `operations/` (Subsystem; importiert nur `models`/`core`):

| Modul | Aufgabe |
|---|---|
| `market_sessions.py` | Definition der Marktsitzungen (Phasen je Markt, Zeitzone) aus der Konfiguration; Validierung von Zeiten/Zeitzonen. |
| `market_clock.py` | Marktuhr: aktuelle Phase, offen/geschlossen, nächste Phase, Countdown, nächste Öffnung – Sommer-/Winterzeit über IANA-Zeitzonen. |
| `scheduler.py` | Bestimmt fällige und nächste Jobs (Uhrzeiten je Zeitzone). |
| `job_queue.py` | Serialisiert Jobs: nur **ein** Discovery gleichzeitig, keine parallelen Vollanalysen, Duplikatschutz. |
| `job_runner.py` | Führt einen injizierten Job aus, misst die Laufzeit, isoliert Fehler (ein Absturz blockiert den Scheduler nie). |
| `job_history.py` | Ringpuffer der letzten Läufe + Kennzahlen (Erfolge/Fehler, Ø Laufzeit). |
| `heartbeat.py` | Lebendigkeit des Systems (letzter Herzschlag vs. Intervall). |
| `health.py` | Gesamtzustand (`OK`/`DEGRADED`/`ERROR`) aus Fehlern/Heartbeat. |
| `system_state.py` | Fasst Health/Heartbeat/Queue/Zähler zum `SystemState` zusammen. |

Engine-Anbindung (`engines/`): `operations_engine.py` (Taktgeber + Regel-Laden),
`operations_registry.py` (bekannte Job-Arten – einzige Erweiterungsstelle),
`operations_cache.py` und `operations_result.py` (Re-Exporte).

## Marktzeiten & Market Clock

Konfigurierte Phasen je Markt (Beispiel-Standard):

- **Europa** (`Europe/Berlin`): Vorbörse 07:30, geöffnet 09:00, Nachmittag 12:00,
  Schluss 17:30.
- **USA** (`America/New_York`): Pre-Market 04:00, Opening Bell 09:30, erste
  Handelsstunde 10:30, Nachmittag 13:00, Schluss 16:00.

Alle Zeiten sind **ausschließlich konfigurierbar**. Sommer-/Winterzeit und
Zeitzonen werden automatisch über die IANA-Zeitzonen berücksichtigt. Die Market
Clock zeigt jederzeit: welche Börsen geöffnet/geschlossen sind, welche als
nächstes öffnet und den Countdown bis zur nächsten Marktphase.

## Automatische Jobs & Scan-Strategie

Der Scheduler startet automatisch (Standard-Zeitplan, konfigurierbar): Europa
Vorbörse/Öffnung/Zwischenanalyse/Schluss sowie US Pre-Market/Opening-Bell/erste
Handelsstunde/Zwischenanalyse/letzte Phase/Tagesabschluss. Bekannte Job-Arten:
`discovery`, `scanner`, `analytics`, `market_intelligence`, `dashboard_refresh`,
`paper_trading_update`, `backtest_refresh`. Jeder Lauf trägt Status, Start-/
Endzeit, Laufzeit, Fehler und Ergebnis.

**Job-Queue:** nur ein Discovery gleichzeitig, keine parallelen Vollanalysen; ein
Fehler blockiert den Scheduler nie; nicht ausgeführte Jobs werden automatisch im
nächsten Takt wieder aufgenommen (automatische Wiederaufnahme).

## OperationReport

Enthält: Marktstatus (alle Märkte), laufende Börsensitzung, letzter erfolgreicher
Scan, nächster Scan, laufender Job, Job-Historie, Systemzustand
(Health/Heartbeat/Queue/Uptime), Anzahl Scans, Anzahl Fehler, Laufzeiten, den
letzten Discovery-Report (Top Opportunities) sowie **neue Chancen** und **neue
Risiken** seit dem letzten Scan. Alle Typen sind unveränderlich (`frozen`) und
**UI-unabhängig**: Desktop-Dashboard, spätere REST-API und mobile Apps nutzen
denselben Report – **keine doppelte Geschäftslogik**.

## Dashboard „Live Operations"

Additiv über Router/Registry (die `DashboardEngine` bleibt unverändert): Marktstatus
Europa/USA mit Countdown, Systemstatus (Health/Heartbeat/Queue/Scans/Fehler/Uptime),
laufender/nächster Job, letzter Scan, Top Opportunities, neue Chancen/Risiken seit
letztem Scan und die Job-Historie. Das Dashboard **liest ausschließlich** den
Report – **keine** Berechnung, keine Geschäfts-/Handelslogik.

## Real-World-Nutzung

Der Benutzer öffnet AlphaAI – ohne Eingaben erscheinen automatisch Marktstatus,
aktive Börsen, Top Opportunities, Ranking, neue Chancen/Risiken, letzter/nächster
Scan und Systemstatus. Europa wird morgens automatisch analysiert; vor der
US-Öffnung erfolgt eine Vorbereitung, nach der Öffnung eine vollständige Analyse.
Die Handelsentscheidung trifft der Benutzer.

## Validierung

Ungültige Marktzeiten/Zeitzonen (Regel-Ladefehler), fehlende Job-Funktionen
(übersprungen), Job-Absturz (isoliert gezählt, Scheduler läuft weiter),
Queue-Duplikate/Exklusivität, doppelte Job-Namen im Zeitplan (Regel-Ladefehler).
Sommer-/Winterzeit wird automatisch korrekt behandelt.

## Performance & Ausblick

Keine unnötigen Neuberechnungen (Jobs laufen nur zu ihren Zeiten; „Incremental
Mode" ist über neue/geänderte Kandidaten vorbereitet). Die zustandslosen,
getrennten Schritte sind auf spätere **Parallelisierung** und eine spätere
**REST-API** vorbereitet – beides ist in diesem Sprint bewusst **noch nicht**
implementiert.

## Erweitern

- **Neue Job-Art:** `JobDefinition` in `operations_registry.py` ergänzen und im
  Zeitplan (`operations_rules.toml`) verwenden; die Job-Funktion injizieren. Die
  Engine bleibt unverändert.
- **Neuer Markt / neue Zeiten:** ausschließlich über
  `knowledge/operations_rules.toml`.
- **Reale Anbindung:** `symbol_source`/`analysis_provider` (Discovery) und die
  Job-Funktionen werden dem `OperationsEngine` injiziert.

## Tests

Über 200 Tests decken Market Sessions, Market Clock (inkl. Sommer-/Winterzeit),
Scheduler, Queue, Runner, History, Heartbeat, Health, System-State, Registry,
Cache, die Engine (Regel-Laden/Tick/Report/Validierung), End-to-End-Börsentage
und die Dashboardseite ab.
