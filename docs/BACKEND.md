# Backend-Dienst (Sprint 17)

Ab Sprint 17 läuft AlphaAI als **produktiver Backend-Dienst**. Sprint 17 bildet
das **endgültige Backend**: Sprint 18 entwickelt ausschließlich die Android-App
und benötigt **keine** Änderungen an den Engines.

Der Backend-Dienst **orchestriert** und **liefert** – er berechnet nichts, trifft
keine Handelsentscheidung und führt keine Orders aus. Die gesamte bestehende
Analyse-Pipeline (MarketDataEngine … Live Operations) bleibt **unverändert**.

## Application Service Layer

Neues Paket `application/` mit klar getrennten Bausteinen:

| Paket | Aufgabe |
| --- | --- |
| `application/exceptions/` | Fehlerhierarchie der Schicht (`ApplicationError` …) |
| `application/serialization/` | wandelt bestehende (frozen) Reports in JSON-fähige Daten |
| `application/repositories/` | dauerhafte Persistenz der Reports (SQLite) |
| `application/responses/` | einheitliche API-Antwort-Hüllen (Envelope) |
| `application/services/` | Lesedienste + Hintergrunddienst |
| `application/health/` | aggregiertes Health-Monitoring |
| `application/authentication/` | vorbereitete Zugriffskontrolle (vorerst lokal) |
| `application/api/` | framework-unabhängige REST-API + FastAPI-Adapter |

**Wichtig:** `application/` importiert ausschließlich `models` und `core`. Die
Pipeline-nahen Engines (insbesondere der Operations-Taktgeber) werden
**injiziert** (Duck-Typing). Dadurch entstehen **keine Import-Zyklen**, und keine
bestehende Engine wird verändert.

## Composition Root: `engines/application_engine.py`

Die `ApplicationEngine` ist die **einzige** Stelle, die sowohl die
`application`-Schicht als auch die Engines kennt. Sie verdrahtet:

- den dauerhaften Report-Speicher (`ReportStore`),
- die Lesedienste (`ReportService`, `SystemService`),
- das Health-Monitoring (`HealthMonitor`),
- die REST-API (`ApplicationApi` + Router),
- den Hintergrunddienst (`BackgroundService`) – sofern ein Operations-Taktgeber
  injiziert wurde.

Die vier Engine-Dateien folgen der etablierten Konvention:
`application_engine.py` (Composition Root + Regel-Laden), `application_registry.py`
(Registry der bekannten Report-Arten – einzige Erweiterungsstelle),
`application_cache.py` (Antwort-Cache) und `application_result.py` (Re-Export der
Modelle).

## Hintergrunddienst

Beim Start werden **Scheduler, Heartbeat, Health-Monitoring, Marktuhr und Live
Operations** aktiviert (der injizierte Operations-Taktgeber leistet dies aus
Sprint 16). Bei jedem Takt:

1. läuft der Operations-Taktgeber (Scheduler/Heartbeat/fällige Jobs),
2. wird der entstandene Operations-Report **dauerhaft gespeichert**,
3. werden zusätzliche Fach-Reports über **injizierte Report-Quellen** bezogen und
   ebenfalls gespeichert.

### Automatische Recovery

Ein Fehler in einem einzelnen Takt oder einer einzelnen Report-Quelle darf den
Dienst **niemals** dauerhaft stoppen. Jeder Schritt ist gekapselt; Fehler werden
gezählt und protokolliert, der Takt läuft weiter. Ein späterer fehlerhafter Takt
löscht **nie** den zuletzt erfolgreich gespeicherten Scan – Dashboard und API
liefern immer den letzten guten Stand.

## Health-Monitoring

Der `HealthMonitor` aggregiert den Zustand aus vorhandenen Werten (keine
Berechnung von Fachdaten):

- **api** – erreichbar,
- **scheduler** – Heartbeat/nächster Scan,
- **market** – offene/geschlossene Märkte,
- **queue** – Warteschlangengröße,
- **cache** – Trefferquote/Größe,
- **system** – Systemzustand/Fehlerzähler,
- **persistence** – Erreichbarkeit/Bestand.

Der Gesamtzustand ist der **schlechteste** Komponentenzustand
(`ok < degraded < error`).

## Konfiguration

Alle Betriebsparameter stammen ausschließlich aus
`knowledge/application_rules.toml` – es gibt **keine hartcodierten Werte**:

```toml
[service]      # Name, Version, API-Version, Umgebung, Beschreibung
[persistence]  # database_file, retention (Schnappschüsse je Art)
[api]          # cache_capacity, default_top_limit, auth_policy
[meta]         # version der Regeldatei
```

## Grenzen (bewusst)

- **Keine** neuen Strategien/Pattern/Scores/Risk-Regeln.
- **Keine** Broker-API, **keine** automatische Orderausführung.
- **Keine** Geschäftslogik in API oder Backend-Dienst – nur Orchestrierung und
  Auslieferung vorhandener Reports.
