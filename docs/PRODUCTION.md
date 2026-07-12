# Produktivbetrieb (Sprint 17)

Dieses Dokument beschreibt, wie AlphaAI als produktiver Backend-Dienst betrieben
wird. Der Dienst **analysiert** und **liefert** Reports – er führt **niemals**
Orders aus. Alle Kauf-/Verkaufsentscheidungen trifft der Benutzer.

## Persistenz (Datenbank)

Alle Reports werden in einer eingebetteten, produktionsgeeigneten
**SQLite-Datenbank** gespeichert (`database/alpha_ai_reports.db`, konfigurierbar
in `knowledge/application_rules.toml`). Eigenschaften:

- **dauerhaft auf der Platte** – überlebt jeden Neustart,
- **keine temporären Dateien**, **keine reine In-Memory-Lösung**,
- transaktional und threadsicher (der Hintergrunddienst schreibt, die API liest),
- **Retention** je Report-Art konfigurierbar (ältere Schnappschüsse werden
  automatisch verworfen; Historie bleibt begrenzt erhalten),
- der jeweils **neueste** Eintrag je Art ist der „letzte erfolgreiche Scan".

Beim Neustart gehen **keine Daten verloren**: Dashboard und API liefern sofort
wieder den zuletzt gespeicherten Stand.

## Start des Dienstes

```python
from engines.application_engine import ApplicationEngine
from engines.operations_engine import OperationsEngine

# 1) Operations-Taktgeber (Sprint 16) mit injizierten Jobs aufbauen.
operations = OperationsEngine.from_config(jobs=..., clock=...)

# 2) Backend-Dienst verdrahten (Persistenz laut Regeln).
engine = ApplicationEngine.from_config(
    operations=operations,
    report_sources={...},  # zusätzliche Fach-Report-Quellen (injiziert)
)

# 3) Starten: Scheduler/Heartbeat/Health/Marktuhr/Live Operations aktiv.
engine.start()

# 4) REST-API bereitstellen (optionaler FastAPI-Adapter).
app = engine.create_fastapi_app()  # uvicorn <modul>:app --host 127.0.0.1
```

Beim Start werden **Scheduler, Heartbeat, Health-Monitoring, Marktuhr und Live
Operations** aktiviert. Danach übernimmt der Dienst die Marktanalysen automatisch
und speichert die Reports dauerhaft.

## Automatische Recovery

- Fehler in einem Takt oder einer Report-Quelle werden **aufgefangen**, gezählt
  und protokolliert; der Dienst läuft weiter.
- Ein fehlerhafter Takt **löscht nie** den letzten erfolgreichen Scan.
- Fehler dürfen den Backend-Dienst **niemals dauerhaft stoppen**.
- Der Betreiber kann den Prozess über einen Prozess-Supervisor (z. B. systemd,
  Docker-Restart-Policy) automatisch neu starten; die Persistenz stellt den
  letzten Stand sofort wieder bereit.

## Health-Überwachung

`GET /api/v1/health` liefert den aggregierten Zustand von API, Scheduler, Markt,
Queue, Cache, System und Persistenz. Der Gesamtzustand ist der schlechteste
Komponentenzustand. Für den Produktivbetrieb kann ein externer Watchdog diesen
Endpunkt periodisch abfragen.

## Validierung & Fehlerfälle

Der Dienst behandelt u. a.:

- ungültige Requests / ungültige Parameter (`400`),
- leere/fehlende Reports und „noch kein Scan" (`503`),
- unbekannte Pfade/Ticker (`404`),
- Scheduler-, Persistenz- und API-Fehler (aufgefangen, protokolliert).

## Sicherheit

- Zugriff **vorerst nur lokal** (`LocalOnlyPolicy`); keine Cloud, keine
  Benutzerverwaltung, keine Registrierung.
- Für den Netzbetrieb ist die Architektur auf zusätzliche Verfahren (Token,
  Benutzer) vorbereitet – ohne die übrige API zu ändern (Open/Closed).

## Frontends

Desktop-Dashboard und Android-App (Sprint 18) greifen **ausschließlich** über die
REST-API auf dieselben Reports zu. Es gibt **keine doppelte Geschäftslogik**.

## Betriebsgrenzen (bewusst)

- **Keine** Broker-Anbindung, **keine** automatische Orderausführung.
- **Keine** Analyse/Berechnung in API oder Backend-Dienst.
- Die Handelsentscheidung trifft **immer** der Benutzer.
