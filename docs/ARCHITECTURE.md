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

## Scanner Core (umgesetzt in Sprint 3)

Der Scanner Core ist reine **Orchestrierung** – er beschafft Marktdaten über
die Data Layer und verpackt sie in Ergebnisobjekte. Er enthält **keine**
Analyse (keine Indikatoren, Muster, Scores oder Handelsentscheidungen).

```
ScannerManager → ScannerEngine → ScanPipeline → MarketDataEngine → (Data Layer)
                                       │
                                 ScanStatistics
```

**Ablauf eines Scans (`ScanPipeline.run`):**

1. Universum laden (falls angegeben) und mit expliziten Symbolen zusammenführen
   (dedupliziert, Reihenfolge erhalten).
2. Für jedes Symbol die `MarketDataEngine` aufrufen.
3. Aus jedem `MarketResult` ein `ScanResult` je Symbol erzeugen (Status,
   Rohdaten, Metadaten, Fehler).
4. Statistik führen (Start/Ende/Laufzeit, Symbolzahl, Provider, Cache-Treffer/
   -Fehltreffer, Fehler).

**Schichtregeln:**

- `ScannerEngine` kennt **ausschließlich** die `ScanPipeline` – keine Provider,
  keine Repositories, keine Indikatoren. Sie ist zugleich der Ort für das
  Scan-Logging (Start, Ende, Universum, Symbolzahl, Laufzeit, Warnungen, Fehler).
- `ScanPipeline` kennt die `MarketDataEngine` und die Universums-Auflösung –
  aber keine Provider/Repositories (die liegen in der Data Layer).
- `ScannerManager` bereitet Läufe über mehrere Märkte/Universen/Zeiträume vor.
  Aktuell **sequenziell**; `max_workers` ist vorbereitet, aber ungenutzt.

**Bausteine:**

| Baustein          | Datei                         | Aufgabe                                          |
|-------------------|-------------------------------|--------------------------------------------------|
| `ScanRequest`     | `scanner/scan_request.py`     | Unveränderliche Anfrage (Markt, Universum, …)    |
| `ScanResult`      | `scanner/scan_result.py`      | Ergebnis je Symbol; Analysefelder vorbereitet    |
| `ScanReport`      | `scanner/scan_result.py`      | Bündelt Einzelergebnisse + Statistik             |
| `ScanStatistics`  | `scanner/scan_statistics.py`  | Kennzahlen des Laufs                             |
| `ScanPipeline`    | `scanner/scan_pipeline.py`    | Orchestrierung (keine Analyse)                   |
| `ScannerEngine`   | `scanner/scanner_engine.py`   | Einstiegspunkt, Logging; kennt nur die Pipeline  |
| `ScannerManager`  | `scanner/scanner_manager.py`  | Mehrfach-Scans (sequenziell, Parallelisierung vorbereitet) |

**Vorbereitete Analysefelder:** `ScanResult` trägt bereits `indicators`,
`patterns`, `score`, `risk`, `recommendation` – im Scanner Core bewusst leer,
Befüllung in späteren Sprints.

**Cache-Statistik:** Das Repository markiert jedes `MarketResult` mit
`metadata["cache_hit"]`; die Pipeline zählt daraus Treffer/Fehltreffer.

## Indicator Engine (umgesetzt in Sprint 4)

Die Indicator Engine berechnet technische Indikatoren aus OHLCV-Daten. Sie
trifft **keine** Handelsentscheidungen, erzeugt **keine** Scores und **keine**
Signale.

```
MarketData → IndicatorEngine → IndicatorResult → Scanner (später)
                  │
      Registry · Cache · Indikatoren (indicators/)
```

**Kernregel:** Jeder Indikator liegt in einer eigenen Datei und ist
**vollständig unabhängig** von den anderen. Ein Indikator liest nur rohe
OHLCV-Daten, nie die Ausgabe eines anderen Indikators. Gemeinsame Hilfsmittel
(z. B. True Range) stehen in `indicators/base.py` – das ist kein Indikator.

**Erweiterbarkeit:** Neue Indikatoren werden ausschließlich über die
`IndicatorRegistry` ergänzt (`register` bzw. `build_default_registry`). Die
Engine kennt nur die Registry, nicht die einzelnen Indikatorklassen (Open/Closed
Principle).

**Bausteine:**

| Baustein            | Datei                            | Aufgabe                                        |
|---------------------|----------------------------------|------------------------------------------------|
| `BaseIndicator`     | `indicators/base.py`             | Schnittstelle + Hilfsfunktionen (kein Indikator) |
| 11 Indikatoren      | `indicators/<name>.py`           | EMA, RSI, ATR, VWAP, MACD, RelativeVolume, ADX, Bollinger, Stochastic, OBV, VolumeProfile |
| `IndicatorRegistry` | `engines/indicator_registry.py`  | Registrierung/Auflösung der Indikatoren        |
| `IndicatorResult`   | `engines/indicator_result.py`    | Aggregat mit typisierten Zugriffen (ema20 …)   |
| `IndicatorCache`    | `engines/indicator_cache.py`     | Cache berechneter Ergebnisse (FIFO)            |
| `IndicatorEngine`   | `engines/indicator_engine.py`    | Orchestrierung, Validierung, Cache             |

**Ergebnis (`IndicatorResult`):** enthält je Indikator die volle Zeitreihe
sowie bequeme Zugriffe (EMA20/50/200, RSI14, ATR14, VWAP, MACD/Signal/
Histogramm, RelativeVolume, ADX, BollingerBands, Stochastic, OBV,
VolumeProfile) plus `calculation_time`, `valid`, `warnings` und `metadata`.

**Validierung:** genug Kerzen (global + je Indikator), NaN in Schlusskursen,
Division durch Null (in den Indikatoren über `safe_divide` abgesichert),
fehlende Volumendaten (volumenabhängige Indikatoren werden dann übersprungen)
und zu wenig Historie.

**Parameter:** ausschließlich aus `knowledge/indicator_rules.toml` – keine
hartcodierten Indikatorparameter im Code.

**Multi-Timeframe:** Die Engine nimmt bereits ein `timeframe`-Label entgegen
(in den Metadaten). Die tatsächliche Mehr-Zeitebenen-Berechnung ist damit
**vorbereitet, aber noch nicht implementiert**.

## Pattern Engine (umgesetzt in Sprint 5)

Die Pattern Engine erkennt Chartmuster aus OHLCV-Daten. Sie trifft **keine**
Handelsentscheidungen, erzeugt **keine** Scores und **keine** Signale.

```
IndicatorResult → PatternEngine → PatternReport (PatternResult je Muster) → Scanner
                       │
             Registry · Cache · patterns/
```

Hinweis: Die Muster arbeiten auf den rohen OHLCV-Daten. Ein optionales
`IndicatorResult` kann übergeben werden (Architektur `IndicatorResult →
PatternEngine`) und wird für spätere, kombinierte Muster in den Metadaten
vermerkt.

**Kernregel** (wie bei den Indikatoren): Jedes Muster liegt in einer eigenen
Datei und ist **vollständig unabhängig** von den anderen. Gemeinsame
Hilfsmittel (Swing-Erkennung, Struktur-Break-Erkennung) und die Ergebnistypen
stehen in `patterns/base.py` – kein Muster hängt von einem anderen ab. Neue
Muster werden ausschließlich über die `PatternRegistry` ergänzt.

**Implementierte Muster (8):** FVG (bullish/bearish, fresh/partially/mitigated,
Gap-Größe & -%), BOS, CHoCH, Equal Highs, Equal Lows, Liquidity Sweep, Market
Structure, Trend Structure (HH/HL/LH/LL + Trend).

**Vorbereitet, ohne Erkennung (3):** Order Block, Breaker Block, Mitigation
Block (`implemented = False`; werden bei aktivierter Config als „vorbereitet"
gemeldet).

**Bausteine:**

| Baustein          | Datei                          | Aufgabe                                        |
|-------------------|--------------------------------|------------------------------------------------|
| `BasePattern`     | `patterns/base.py`             | Schnittstelle, Typen, Hilfen (kein Muster)     |
| 11 Muster         | `patterns/<name>.py`           | je ein Detektor                                |
| `PatternResult`   | `patterns/base.py`             | ein erkanntes Muster (Name, Typ, Richtung, Strength 0-100, Confidence 0-1, Timestamp, Price Level, Metadata) |
| `PatternReport`   | `engines/pattern_result.py`    | Aggregat + Lauf-Metadaten                      |
| `PatternRegistry` | `engines/pattern_registry.py`  | Registrierung/Auflösung                        |
| `PatternCache`    | `engines/pattern_cache.py`     | Cache erkannter Muster (FIFO)                  |
| `PatternEngine`   | `engines/pattern_engine.py`    | Orchestrierung, Validierung, Cache             |

**Validierung:** genug Kerzen, ungültige Muster (Parameterfehler), überlappende
Muster (Zählung überlappender FVG-Zonen), ungültige Zeitreihen (Index nicht
eindeutig/sortiert) sowie NaN in Schlusskursen.

**Parameter:** ausschließlich aus `knowledge/pattern_rules.toml`.

## Strategy Engine (umgesetzt in Sprint 6)

Die Strategy Engine kombiniert Indikatoren und Muster zu objektiven
**Handelshypothesen**. Sie trifft **keine** Kauf-/Verkaufsentscheidung und
vergibt **keinen** Gesamtscore.

```
IndicatorResult + PatternReport → StrategyEngine → StrategyReport (StrategyResult je Hypothese) → ScoreEngine (später)
                       │
             Registry · Cache · strategies/
```

**Kernregel** (wie bei Indikatoren/Mustern): Jede Strategie liegt in einer
eigenen Datei und ist **unabhängig** von den anderen. Die gemeinsame
Schnittstelle und die Ergebnistypen stehen in `strategies/base.py`. Neue
Strategien werden ausschließlich über die `StrategyRegistry` ergänzt.

**Implementierte Strategien (5):** `fvg_strategy` (FVG + EMA200-Trendfilter),
`trend_following` (EMA-Fächer + ADX), `momentum_strategy` (RSI + MACD),
`breakout_strategy` (BOS + relatives Volumen), `mean_reversion` (RSI-Extrem +
Bollinger-Band).

**Jede Strategie besitzt:** Name, Beschreibung, Version, Konfiguration,
Pattern-Anforderungen, Indikator-Anforderungen und (aus der Konfiguration) eine
Confidence.

**Bausteine:**

| Baustein           | Datei                           | Aufgabe                                        |
|--------------------|---------------------------------|------------------------------------------------|
| `BaseStrategy`     | `strategies/base.py`            | Schnittstelle, Typen, Hilfen                   |
| 5 Strategien       | `strategies/<name>.py`          | je eine Hypothesen-Logik                       |
| `StrategyResult`   | `strategies/base.py`            | eine Hypothese (Name, ID, Richtung, Confidence, Strength, matched indicators/patterns, Reasons, Warnings, Metadata, Timestamp) |
| `StrategyReport`   | `engines/strategy_result.py`    | Aggregat + Lauf-Metadaten                      |
| `StrategyRegistry` | `engines/strategy_registry.py`  | Registrierung/Auflösung                        |
| `StrategyCache`    | `engines/strategy_cache.py`     | Cache (FIFO)                                   |
| `StrategyEngine`   | `engines/strategy_engine.py`    | Kombination, Validierung, Cache                |

**Hypothesen statt Entscheidungen:** Jede Strategie erzeugt eine Hypothese wie
„Bullische Trendfortsetzung" (in `metadata['hypothesis']` und `reasons`) – nie
eine Kaufempfehlung. Strength/Confidence sind beschreibende Kennzahlen der
Hypothese, kein Gesamtscore.

**Validierung:** fehlende/ungültige Indikator- oder Musterdaten, fehlende
Indikator-Anforderungen, fehlende Muster-Anforderungen und inkonsistente
Ergebnisse (abweichender Timeframe/Kerzenzahl).

**Parameter:** ausschließlich aus `knowledge/strategy_rules.toml`.

## Score Engine (umgesetzt in Sprint 7)

Die Score Engine bewertet jede Hypothese (`StrategyResult`) **objektiv**. Sie
trifft **keine** Kauf-/Verkaufsentscheidung, erzeugt **keine** Positionsgröße
und **kein** Risiko.

```
StrategyReport → ScoreEngine → ScoreReport (ScoreResult je Hypothese) → RiskEngine (später)
                     │
        Registry · Cache · scores/ · 8 Komponenten
```

**Acht Komponenten** (in `scores/base.py` berechnet, je Score getrennt
gespeichert): Trend, Momentum, Pattern Strength, Pattern Confidence, Indicator
Quality, Market Context, Volume Quality, Data Quality.

**Fünf Score-Modelle** (je eigene Datei, unabhängig voneinander):
`weighted_score` (Gesamtscore 0-100 aus allen Komponenten), `confidence_score`
(0-1), `quality_score` (0-100), `consensus_score` (0-100), `market_score`
(0-100). Neue Modelle werden ausschließlich über die `ScoreRegistry` ergänzt;
die Engine bleibt unverändert (unbekannte Modelle erscheinen zusätzlich in
`metadata['model_scores']`).

**Transparenz:** Jeder Score ist über seine Komponenten vollständig erklärbar.
Der Weighted Score liefert je Komponente einen Beitrag im Format
`trend: 18/20`; alle Komponenten-Erklärungen und Modell-Begründungen stehen in
`ScoreResult.reasons`.

**Bausteine:**

| Baustein         | Datei                         | Aufgabe                                        |
|------------------|-------------------------------|------------------------------------------------|
| `BaseScoreModel` | `scores/base.py`              | Schnittstelle, Typen, Komponenten, Gewichtsvalidierung |
| 5 Score-Modelle  | `scores/<name>.py`            | je ein Aggregat-Score                          |
| `ScoreResult`    | `engines/score_result.py`     | Bewertung einer Hypothese (Score ID, Strategy Name, Hypothesis ID, Total/Confidence/Quality/Consensus/Market, Component Scores, Reasons, Warnings, Metadata, Timestamp) |
| `ScoreReport`    | `engines/score_result.py`     | Aggregat + Lauf-Metadaten                      |
| `ScoreRegistry`  | `engines/score_registry.py`   | Registrierung/Auflösung                        |
| `ScoreCache`     | `engines/score_cache.py`      | Cache (FIFO)                                   |
| `ScoreEngine`    | `engines/score_engine.py`     | Bewertung, Validierung, Cache                  |

**Validierung:** fehlende Hypothesen, ungültige Gewichte, Gewichte ≠ 100 %,
fehlende Komponenten (jeweils über `validate_weights` bzw. die Engine).

**Gewichte:** ausschließlich aus `knowledge/score_rules.toml`.

## Aktueller Stand

Sprint 1–7 sind abgeschlossen (Fundament, Data Layer, Scanner Core, Indicator
Engine, Pattern Engine, Strategy Engine, Score Engine). Es gibt bewusst
weiterhin **keine Risk-Engine, keine Recommendation-Engine und keine
Dashboard-Logik**.
