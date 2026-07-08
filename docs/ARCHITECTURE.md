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

## Data Layer (umgesetzt in Sprint 2)

Die Data Layer beschafft, prüft und cached Marktdaten. Sie ist strikt
geschichtet; jede Ebene kennt nur die direkt darunterliegende:

```
MarketDataEngine  →  MarketRepository  →  Provider  →  (externe Quelle)
                              │
                        Cache + Validator
```

**Datenfluss einer Anfrage:**

1. Ein `MarketRequest` (Symbole, Zeitraum, Intervall, Markt, Cache-Flag)
   beschreibt die Anfrage unveränderlich.
2. Die `MarketDataEngine` ergänzt Standardwerte aus der Konfiguration und löst
   bei Bedarf ein Universum in Symbole auf.
3. Das `MarketRepository` prüft zuerst den `TTLCache`. Bei Fehltreffer lädt es
   über den `Provider`, validiert das Ergebnis und legt brauchbare Daten im
   Cache ab.
4. Das Resultat ist ein `MarketResult` mit kanonischem OHLCV-Schema, Status
   (`OK`/`PARTIAL`/`EMPTY`/`ERROR`), Metadaten und Fehlerliste.

**Bausteine:**

| Baustein            | Datei                                   | Aufgabe                                              |
|---------------------|-----------------------------------------|------------------------------------------------------|
| `MarketRequest`     | `data/market_request.py`                | Unveränderliche Anfrage inkl. Cache-Schlüssel        |
| `MarketResult`      | `data/market_result.py`                 | Ergebnis mit festem OHLCV-Schema und Status          |
| `TTLCache`          | `data/cache.py`                         | Cache mit kategoriespezifischer TTL                  |
| `MarketDataValidator` | `data/validator.py`                   | Qualitätsprüfung (zerstörungsfrei)                   |
| `Universe`          | `data/universe.py`                      | Symbollisten je Markt (aus `config/universe.toml`)   |
| `BaseProvider`      | `providers/base_provider.py`            | Gemeinsame Provider-Schnittstelle                    |
| `YahooProvider`     | `providers/yahoo_provider.py`           | Yahoo-Finance-Quelle (yfinance)                      |
| `provider_factory`  | `providers/provider_factory.py`         | Provider-Erzeugung nach Name                         |
| `MarketRepository`  | `repositories/market_repository.py`     | Kapselt Provider + Cache + Validator                 |
| `repository_factory`| `repositories/repository_factory.py`    | Verdrahtung aus der Konfiguration (Composition Root) |
| `MarketDataEngine`  | `data/market_data_engine.py`            | Fachnahe Zugriffsschicht (kennt nur das Repository)  |

**Provider-Strategie:** Implementiert ist `yahoo`. Vorbereitet (per Factory
bekannt, aber bewusst nicht implementiert) sind `finnhub`, `polygon`,
`alphavantage`, `iex`; ihr Abruf löst einen klaren Fehler aus, statt falsche
Daten zu liefern.

**Testbarkeit durch Dependency Injection:** Netzwerk (Download-Funktion) und
Zeit (Cache-Uhr) sind injizierbar. Dadurch ist die gesamte Data Layer ohne
echte Netzwerkverbindung und ohne Warten testbar.

**Cache-Kategorien:** historische Daten, Intraday-Daten und Tickerlisten haben
je eine eigene, in `[data.cache]` konfigurierte TTL.

**Validator-Prüfungen:** NaN, nicht-positive Preise, doppelte/unsortierte
Zeitstempel (Fehler) sowie fehlende Kerzen (Warnung, da Wochenenden/Feiertage
noch nicht kalendergenau berücksichtigt werden) und ungültige Symbolformate.

## Aktueller Stand

Sprint 1 lieferte das Fundament, Sprint 2 die vollständige Data Layer. Es gibt
bewusst weiterhin **keinen Scanner, keine Indikatoren (EMA/RSI/FVG), keine
Scores und keine Handelslogik**.
