# Architektur

Dieses Dokument beschreibt den Aufbau von Alpha AI. Es richtet sich auch an
Leser ohne Programmiererfahrung und wird nach jedem Sprint aktualisiert.

## Leitgedanke

Alpha AI ist in **Schichten** aufgebaut. Jede Schicht hat genau eine Aufgabe
und kennt nur die Schichten unter sich. Das macht das System verständlich,
testbar und erweiterbar (Clean Architecture, SOLID).

```
        Dashboard (Streamlit)         ← zeigt Ergebnisse
              │
        Scanner (Orchestrierung)      ← führt die Analyse zusammen
        ┌─────┼───────────────┐
     Engines  Patterns   Strategies   ← Fachlogik der Analyse
        └─────┼───────────────┘
        Data / Providers              ← Marktdaten beschaffen
              │
        Database (SQLite)             ← speichert Ergebnisse
              │
        Core (Config, Logging, …)     ← technische Grundlage
```

Regel: **Abhängigkeiten zeigen nur nach unten.** Die Kernschicht (`core`)
kennt keine Fachlogik. Dadurch bleibt sie stabil.

## Schichten im Detail

| Schicht      | Paket        | Verantwortung                                        |
|--------------|--------------|------------------------------------------------------|
| Kern         | `core`       | Konfiguration, Logging, Pfade, Fehlerklassen         |
| Domäne       | `models`     | Gemeinsame Datenstrukturen (Setup, Empfehlung, …)    |
| Daten        | `data`       | Modelle & Zugriff auf Marktdaten                     |
| Datenquellen | `providers`  | Kapselung externer Quellen (z. B. yfinance)          |
| Analyse      | `engines`    | Technische Kennzahlen/Indikatoren                    |
| Muster       | `patterns`   | Erkennung von Kursmustern                            |
| Strategien   | `strategies` | Bewertung von Setups                                 |
| Orchestr.    | `scanner`    | Zusammenführen der Analyse                            |
| Persistenz   | `database`   | Speichern/Laden (SQLite)                             |
| Präsentation | `dashboard`  | Streamlit-Oberfläche, Plotly-Charts                  |

## Konfiguration (umgesetzt in Sprint 1)

- Alle Parameter liegen in `config/settings.toml`.
- `core/config.py` lädt die Datei mit der Standardbibliothek (`tomllib`) und
  überführt sie in typisierte, **unveränderliche** Datenklassen.
- Fehlende oder unplausible Werte führen sofort zu einem klaren Fehler
  (`ConfigError`, Fail-Fast). Es gibt **keine hartcodierten Werte** im Code.

## Logging (umgesetzt in Sprint 1)

- `core/logging_config.py` richtet Logging einmalig ein (idempotent).
- Ausgabe erfolgt gleichzeitig auf Konsole und in eine rotierende Datei
  (`logs/alpha_ai.log`).

## Dependency Injection (vorbereitet)

Die Konfiguration wird als Objekt erzeugt und an abhängige Komponenten
**übergeben**, statt global gelesen zu werden. Fachmodule erhalten Daten und
Konfiguration künftig über ihre Konstruktoren/Parameter. Das erleichtert
Tests (Austausch durch Attrappen) und entkoppelt die Schichten.

## Wissensbasis

Regeln und Parameter der Analyse leben in `knowledge/` (Markdown für
Erklärungen, TOML für Parameter). Dadurch lassen sich Indikatoren, Muster und
Strategien anpassen, ohne Programmcode zu ändern.

## Aktueller Stand

Sprint 1 liefert ausschließlich das Fundament (Struktur, Konfiguration,
Logging, Tests, Dokumentation). Es gibt bewusst noch **keinen Scanner, keine
Datenquellen, keine Indikatoren und keine Handelslogik**.
