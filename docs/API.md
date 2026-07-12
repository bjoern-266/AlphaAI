# REST-API (Sprint 17)

Die AlphaAI-REST-API stellt **ausschließlich vorhandene Reports** als JSON
bereit. Sie führt **keine** Analyse aus, **berechnet nichts**, erzeugt **keine**
Scores/Risiken/Empfehlungen und trifft **keine** Handelsentscheidung. Alle
Kauf-/Verkaufsentscheidungen trifft der Benutzer.

Die API ist die **einzige** Schnittstelle für alle Frontends: das
Desktop-Dashboard und die spätere Android-App (Sprint 18) greifen ausschließlich
über dieselbe API auf dieselben Reports zu – keine doppelte Geschäftslogik.

## Architektur

```
Live Operations → Persistenz (SQLite) → Report Service → REST API → Frontends
```

Der Kern der API (Routing, Request/Response, Fehlerbehandlung, Cache) ist
**framework-unabhängig** und vollständig getestet. Ein dünner FastAPI-/uvicorn-
Adapter (`application/api/service.py`) bindet die API bei Bedarf an HTTP an; er
enthält keinerlei Fachlogik. Diese Trennung entspricht dem streamlit-freien
Dashboard.

## Versionierung

Alle Endpunkte liegen unter dem Präfix `/api/v1`. Die API-Version steht in den
Antwort-Metadaten (`meta.api_version`). Neue Versionen erhalten ein neues Präfix;
bestehende bleiben stabil.

## Antwortformat (Envelope)

Jede Antwort – Erfolg wie Fehler – hat dieselbe äußere Struktur:

```json
{
  "ok": true,
  "data": { "...": "die eigentlichen Report-Daten" },
  "error": null,
  "meta": {
    "api_version": "v1",
    "generated_at": "2026-07-12T14:30:00+00:00",
    "kind": "operations"
  }
}
```

Fehlerantwort:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "status": 404,
    "code": "not_found",
    "message": "Keine Chance für Ticker 'ZZZ' gefunden.",
    "detail": { "ticker": "ZZZ" }
  },
  "meta": { "api_version": "v1", "generated_at": "..." }
}
```

Alle Antworten sind **ausschließlich JSON**. Große Antworten werden vom
FastAPI-Adapter per GZip komprimiert (falls der Client `Accept-Encoding: gzip`
sendet).

## Endpunkte

Alle Endpunkte sind `GET` (die API ist lesend – sie verändert nichts).

### System

| Pfad | Beschreibung | Quelle |
| --- | --- | --- |
| `/health` | Aggregierter Gesundheitszustand (API/Scheduler/Markt/Queue/Cache/System/Persistenz) | Health-Monitor |
| `/status` | Kompakte Statuszusammenfassung (Uptime, gespeicherte Reports, Systemzustand) | System-Service |
| `/version` | Version und Beschreibung des Dienstes | System-Service |
| `/scheduler` | Zustand des Schedulers (nächster/laufender Scan, Historie) | Operations-Report |
| `/operations` | Vollständiger Operations-Report der Live Operations Platform | Operations-Report |

### Märkte

| Pfad | Beschreibung | Quelle |
| --- | --- | --- |
| `/markets` | Zustände aller Märkte (offen/geschlossen) | Operations-Report |
| `/market-status` | Zusammengefasste Marktuhr (offene Märkte, nächste Öffnung) | Operations-Report |
| `/opportunities` | Vollständiger Opportunity-Report (Market Intelligence) | Opportunity-Report |
| `/opportunities/top` | Beste Chancen nach Ranking (`?limit=N`, Standard 10) | Opportunity-Report |
| `/opportunities/{ticker}` | Chance zu einem einzelnen Ticker | Opportunity-Report |
| `/discovery` | Vollständiger Market-Discovery-Report | Discovery-Report |

### Empfehlungen

| Pfad | Beschreibung | Quelle |
| --- | --- | --- |
| `/recommendations` | Vollständiger Recommendation-Report | Recommendation-Report |
| `/recommendations/{ticker}` | Empfehlung zu einem einzelnen Ticker (aus den Chancen-Reports) | Opportunity/Discovery |

### Analytics

| Pfad | Beschreibung | Quelle |
| --- | --- | --- |
| `/analytics` | Vollständiger Analytics-Report | Analytics-Report |
| `/backtesting` | Vollständiger Backtesting-Report | Backtest-Report |
| `/paper-trading` | Vollständiger Paper-Trading-Report | Paper-Trading-Report |

### Dashboard

| Pfad | Beschreibung | Quelle |
| --- | --- | --- |
| `/dashboard` | Zusammengesetzter Schnappschuss aller Reports (dieselbe Quelle wie die App) | Alle Reports |

## Statuscodes

| Code | Bedeutung |
| --- | --- |
| `200` | Erfolg |
| `400` `invalid_request` | Ungültiger Parameter (z. B. `limit=abc`) |
| `401` `unauthorized` | Zugriff verweigert (aktuell: nur lokaler Host) |
| `404` `not_found` | Unbekannter Pfad oder Ticker |
| `405` | Methode nicht erlaubt |
| `503` `service_unavailable` | Noch kein erfolgreicher Scan vorhanden |

Der Dienst bleibt bei ungültigen Anfragen stets stabil und antwortet
wohlgeformt.

## Zugriffskontrolle

Die Zugriffskontrolle ist auf spätere Erweiterungen (Token, Benutzer, Cloud)
**vorbereitet**, erlaubt aber **vorerst ausschließlich lokalen Zugriff**
(`LocalOnlyPolicy`). Es gibt keine Benutzerverwaltung, keine Registrierung und
keine Cloud. Neue Verfahren implementieren den `AuthPolicy`-Vertrag, ohne die
übrige API zu verändern (Open/Closed).

## Caching & Performance

- Antworten werden pro `(Methode, Pfad, Query)` **revisionsgebunden**
  zwischengespeichert. Sobald ein neuer Report gespeichert wird, ändert sich die
  Speicher-Revision und der Cache liefert automatisch den frischen Stand – es
  wird **nie** ein veralteter Scan ausgeliefert.
- Der FastAPI-Adapter komprimiert große Antworten (GZip).
- Die ticker- und Top-N-Endpunkte liefern nur die benötigten Teilmengen.

## Android-Vorbereitung (Sprint 18)

Die Android-App verwendet später **ausschließlich HTTP-Requests** gegen diese
API. Sie darf **niemals** direkt Engines verwenden und enthält keine
Python-Logik. Das einheitliche Envelope-Format, die stabile Versionierung und die
reinen JSON-Antworten sind darauf ausgelegt.

## Betrieb

Die FastAPI-App wird über die Engine gebaut:

```python
from engines.application_engine import ApplicationEngine

engine = ApplicationEngine.from_config(operations=..., report_sources=...)
engine.start()
app = engine.create_fastapi_app()  # uvicorn app:app
```

Details zum Hintergrunddienst siehe [BACKEND.md](BACKEND.md), zum produktiven
Betrieb siehe [PRODUCTION.md](PRODUCTION.md).
