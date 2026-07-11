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
        Models (Entities)             ← unveränderliche Datentypen
              │
        Core (Config, Logging, …)     ← technische Grundlage
```

Regel: **Abhängigkeiten zeigen nur nach unten.** Die Kernschicht (`core`)
kennt keine Fachlogik. Die Entities-Schicht (`models`) enthält ausschließlich
unveränderliche Datentypen und importiert nichts aus höheren Schichten.
Dadurch bleiben beide stabil.

## Schichten im Detail

| Schicht      | Paket        | Verantwortung                                        |
|--------------|--------------|------------------------------------------------------|
| Kern         | `core`       | Konfiguration, Logging, Pfade, Fehlerklassen         |
| Domäne       | `models`     | Unveränderliche Ergebnistypen (market/indicator/…)   |
| Daten        | `data`       | Modelle & Zugriff auf Marktdaten                     |
| Datenquellen | `providers`  | Kapselung externer Quellen (z. B. yfinance)          |
| Analyse      | `engines`    | Technische Kennzahlen/Indikatoren                    |
| Muster       | `patterns`   | Erkennung von Kursmustern                            |
| Strategien   | `strategies` | Bewertung von Setups                                 |
| Risiko       | `risk`       | Risikomodelle & Positionsgröße (keine Order)         |
| Empfehlung   | `recommendation` | Objektive Handlungsempfehlung (keine Order)      |
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

## Architektur-Konsolidierung (umgesetzt in Sprint 7.5)

Verhaltenserhaltender Umbau, der das Fundament vor den nächsten Fachschichten
festigt (Tag `v0.1.0-foundation`). Vier Bausteine:

1. **Domänenmodelle in `models/`.** Alle Ergebnis-/Datentypen liegen in der
   Entities-Schicht: `models/market.py`, `models/indicator.py`,
   `models/pattern.py`, `models/strategy.py`, `models/score.py`
   (`models/risk.py`, `models/recommendation.py` vorbereitet). Die bisherigen
   Pfade (`data.market_result`, `engines/*_result.py`, `*/base.py`)
   **re-exportieren** diese Typen – bestehender Code bleibt unverändert gültig.
   Dadurch importieren `strategies`/`scores` nichts mehr aus `engines`.

2. **Unveränderliche Ergebnisobjekte.** Jedes Modell ist eine `frozen`
   Dataclass. Die Engines bauen ihr Ergebnis aus lokalen Akkumulatoren auf und
   konstruieren es **einmalig am Ende**; die Rechenzeit wird über
   `dataclasses.replace()` gesetzt. Kein Ergebnis wird nach der Erstellung
   verändert.

3. **Generische Basis in `core/`.** `core/cache.py` (`Cache[T]`, FIFO,
   Trefferzählung) und `core/registry.py` (`Registry[T]`) bündeln die zuvor
   vierfach duplizierte Logik. Die Engine-Caches/-Registries sind nur noch
   dünne Spezialisierungen mit unverändertem öffentlichem Verhalten.

4. **Einheitliche Fehler.** Alle fachlichen Fehler stammen aus `AlphaAIError`
   (`core/exceptions.py`): `ParameterError`, `RegistryError`, `CacheError` und
   ihre Unterklassen. Für Rückwärtskompatibilität erben ausgewählte Klassen
   zusätzlich von `ValueError`/`KeyError`.

Abgesichert durch `scripts/quality_check.py` (0 Import-Zyklen, saubere
Entities-Schicht, Plugin-Unabhängigkeit, SOLID) – fest verankert in
`tests/test_quality.py`.

## Risk Engine (umgesetzt in Sprint 8)

Die Risk Engine bewertet das Risiko jeder bewerteten Hypothese und empfiehlt
eine Positionsgröße. Sie trifft **keine** Kauf-/Verkaufsentscheidung, eröffnet
**keine** Position und sendet **keine** Order.

```
ScoreReport → RiskEngine → RiskReport (RiskResult je Score) → RecommendationEngine (später)
                  │
     Registry · Cache · risk/ · 10 Komponenten · Positionsgröße
```

**Zehn Risikokomponenten** (getrennt gespeichert, je Beitrag `name: 18/25`):
Volatilität, Liquidität, Gap, Spread, ATR, Markt, Korrelation,
Portfolio-Exposure, Datenqualität, News (News **vorbereitet**, neutral). Sieben
liefern Modelle, drei sind Basiskomponenten (ATR, Datenqualität, News) in
`risk/base.py`. Das Gesamtrisiko (0-100) ist ihre gewichtete Summe; daraus folgt
die Stufe LOW/MEDIUM/HIGH.

**Acht Risk-Modelle** (je eigene Datei, unabhängig): `position_sizing`
(Positionsgröße/Order/Kosten, ohne Risikobeitrag), `volatility_risk`,
`liquidity_risk`, `gap_risk`, `market_risk`, `correlation_risk` (vorbereitet),
`portfolio_risk` (vorbereitet), `execution_risk`. Neue Modelle nur über die
`RiskRegistry`; die Engine bleibt unverändert.

**Positionsgröße:** aus `settings.toml` (Depotgröße, Fractional Shares, Risiko je
Trade, max. Positionen) und `risk_rules.toml` (ATR-Stop, CRV, Slippage/Kommission,
Positions-/Portfolio-Obergrenzen). **Portfolio-Vorbereitung:** der `RiskContext`
führt `open_positions`, sodass Portfolio-/Korrelationsrisiko ohne Engine-Änderung
voll implementiert werden kann.

**Bausteine:**

| Baustein        | Datei                        | Aufgabe                                        |
|-----------------|------------------------------|------------------------------------------------|
| `BaseRiskModel` | `risk/base.py`               | Schnittstelle, Positionsgröße, Basiskomponenten, Gewichte |
| 8 Risk-Modelle  | `risk/<name>.py`             | je ein Risikoaspekt bzw. die Positionsgröße    |
| `RiskResult`    | `models/risk.py`             | Risikobewertung einer Hypothese (Overall Risk, Level, Positionsgröße, Kosten, Stop/TP/CRV, Komponenten, Reasons, Warnings, Metadata, Timestamp) |
| `RiskReport`    | `models/risk.py`             | Aggregat + Lauf-Metadaten                      |
| `RiskRegistry`  | `engines/risk_registry.py`   | Registrierung/Auflösung                        |
| `RiskCache`     | `engines/risk_cache.py`      | Cache (FIFO)                                   |
| `RiskEngine`    | `engines/risk_engine.py`     | Bewertung, Validierung, Cache                  |

**Validierung:** fehlende Scores, negative Depotgröße, ungültige ATR/Preise,
ungültige Positionsgrößen, ungültige Risk-Reward-Werte.

**Parameter:** ausschließlich aus `knowledge/risk_rules.toml` (Modelle/Gewichte/
Schwellen) und `config/settings.toml` (Konto/Depot). Keine Hardcodes.

## Recommendation Engine (umgesetzt in Sprint 9)

Die Recommendation Engine ist die **letzte fachliche Entscheidungsschicht**. Sie
kombiniert Strategie, Score und Risiko je Hypothese zu einer objektiven,
vollständig erklärbaren Empfehlung. Sie eröffnet **keine** Position, sendet
**keine** Order und kommuniziert **nicht** mit Brokern.

```
StrategyReport + ScoreReport + RiskReport → RecommendationEngine → RecommendationReport
                          │
        Registry · Cache · recommendation/ · 6 Faktoren · No-Trade-Gates
```

**Sechs Entscheidungsfaktoren** (in `recommendation/base.py` berechnet):
Strategie, Score, Risiko, Konsens, Marktqualität, Datenqualität. Das
Gesamtrating (0-100) ist ihre gewichtete Summe; daraus folgt die **Stärke**
VERY_HIGH/HIGH/MEDIUM/LOW/REJECT und die Handlung OPEN/WAIT/MONITOR/SKIP. Die
**Richtung** (LONG/SHORT/NEUTRAL) wird getrennt geführt (seit Sprint 9.6) und
folgt der Strategie-Hypothese – die Stärke impliziert nie eine Richtung.

**No-Trade-Philosophie** („Kein Trade ist besser als ein schlechter Trade."):
Der Score-Anteil ist bewusst begrenzt, der Konsens belohnt **Breite** (mehrere
unabhängige, gleichgerichtete Strategien), und **Gates** deckeln bei erhöhtem
Risiko, geringem Konsens, schwacher Datenqualität oder neutraler Richtung. Ein
hoher Score allein führt daher **nie** zu hoher Stärke (HIGH/VERY_HIGH);
`LOW`/`REJECT` sind vollwertige Empfehlungen. Ein bärisches Setup ist **SHORT**
mit ggf. hoher Stärke – nie „BUY".

**Fünf Modelle** (je eigene Datei, unabhängig): `decision_model` (Rating +
Faktor-Transparenz), `recommendation_model` (Stufe/Handlung + Gates),
`confidence_model` (0-1), `summary_model` (Kurzfassung), `explanation_model`
(Reasons/Warnings). Neue Modelle nur über die `RecommendationRegistry`.

**Transparenz:** Jede Empfehlung trägt Reasons, Warnings und Summary – keine
Blackbox. Parameter ausschließlich aus `knowledge/recommendation_rules.toml`.

**Bausteine:**

| Baustein                 | Datei                                   | Aufgabe                          |
|--------------------------|-----------------------------------------|----------------------------------|
| `BaseRecommendationModel`| `recommendation/base.py`                | Schnittstelle, Faktoren, Gates   |
| 5 Modelle                | `recommendation/<name>.py`              | je ein Aspekt der Empfehlung     |
| `RecommendationResult`   | `models/recommendation.py`              | Empfehlung einer Hypothese (Direction, Strength, Action, Confidence, Rating, Reasons, Warnings, Summary, Metadata, Timestamp) |
| `RecommendationReport`   | `models/recommendation.py`              | Aggregat + Lauf-Metadaten        |
| `RecommendationRegistry` | `engines/recommendation_registry.py`    | Registrierung/Auflösung          |
| `RecommendationCache`    | `engines/recommendation_cache.py`       | Cache (FIFO)                     |
| `RecommendationEngine`   | `engines/recommendation_engine.py`      | Kombination, Validierung, Cache  |

**Validierung:** fehlender/ungültiger Strategy-/Score-/Risk-Report, fehlende
Zuordnung je Hypothese, ungültige Level/Confidence/Ratings.

## End-to-End-Integration (umgesetzt in Sprint 9.5)

Der `IntegrationRunner` (`pipeline/runner.py`) verbindet alle sieben Stufen zu
einem vollständigen Durchlauf und liefert ein unveränderliches `PipelineResult`
(`models/pipeline.py`). Er enthält **keine** neue Fachlogik: jede Engine erhält
nur vorgelagerte Ausgaben (Indikatoren/Muster sind gemeinsame Vorstufen).

```
MarketData → Indicator → Pattern → Strategy → Score → Risk → Recommendation
                              │
                    IntegrationRunner (pipeline/)
                              │
                        PipelineResult
```

`pipeline.consistency.verify_pipeline` prüft automatisch: jede Empfehlung → genau
ein Risk → genau ein Score → genau eine Strategie; alle IDs eindeutig, alle
Referenzen gültig. Validiert über 13 echte Szenarien und 180 Integrations-Tests
(kein Mock). Details: `docs/PIPELINE.md`, `docs/VALIDATION_REPORT.md`.

## Historical Backtesting Framework (umgesetzt in Sprint 10)

Das Backtesting-Subsystem (`backtesting/`) hängt **nur hinten** an die
bestehende Pipeline an und bewertet **rein**, wie sich die daraus entstehenden
Empfehlungen historisch entwickelt hätten. Es erzeugt **keine** neue
Handelsregel, ändert **keine** Engine und führt **keine** echte Order aus
(Trades werden ausschließlich rechnerisch simuliert).

```
Historische Marktdaten
        │
IntegrationRunner (bestehende Pipeline, fensterweise, kein Look-Ahead)
        │
HistoricalRunner → HistoricalSignal(e)
        │
TradeSimulator → SimulatedTrade(s)   (Entry/Exit/Stop/Take-Profit, Fractional
        │                             Shares, Kosten; Risiko aus settings.toml)
BacktestEngine (+ BacktestRegistry/-Cache) → BacktestReport / BacktestResult
```

- **Schicht-Einordnung:** `backtesting/` ist – wie `pipeline/` – ein Subsystem,
  keine Plugin-Familie mit Unabhängigkeitsprüfung; die Hilfsmodule
  (`historical_runner`, `trade_simulator`, `performance_metrics`,
  `equity_curve`, `statistics`, `benchmark`) arbeiten zusammen. In
  `quality_check.py` unterliegt es der Zyklenprüfung (0 Zyklen). Die
  Kennzahlgruppen sind **Registry-Plugins** (`performance_model`,
  `drawdown_model`, `ratio_model`, `benchmark_model`) – neue nur über
  `engines/backtest_registry.py`, die Engine bleibt unverändert (Open/Closed).
- **Entities:** `models/backtest.py` (alle `frozen`), re-exportiert über
  `engines/backtest_result.py`.
- **Kein Look-Ahead:** an jedem Auswertungspunkt sieht die Pipeline nur die
  Kerzen bis einschließlich dieses Punkts (`frame.iloc[:i+1]`).
- **Validierung:** ungültige Zeiträume, fehlende Daten, leere Historie,
  ungültige Preise und ungültige Kennzahlen (nicht-endlich; Profit Factor `inf`
  ohne Verluste ist ein zulässiger Sonderfall).
- **Benchmark:** optionaler Buy-&-Hold-Vergleich (Referenz, keine Empfehlung).
- **Vorbereitet:** Sharpe/Sortino/Calmar sind implementiert, aber nicht
  annualisiert/kalibriert (`None` bei zu wenig Daten). Details:
  `docs/BACKTESTING.md`.

## Paper Trading Framework (umgesetzt in Sprint 11)

Das Paper-Trading-Subsystem (`paper_trading/`) hängt – wie das Backtesting –
**nur hinten** an die bestehende Pipeline an und bewertet **rein**, wie sich die
Empfehlungen unter (simulierten) Live-Bedingungen mit einem **simulierten**
Portfolio entwickeln. Es führt **niemals** echte Orders aus, hat **keine**
Broker-API und ändert **keine** Engine oder das Backtesting.

```
Live-Marktdaten
        │
IntegrationRunner (bestehende Pipeline, tagweise, kein Look-Ahead)
        │
PaperRunner → Empfehlung → PaperPortfolio (open/mark/close/expire)
        │
PaperTradingEngine (+ Registry/Cache) → PaperTradingReport / PaperTradingResult
```

- **Schicht-Einordnung:** `paper_trading/` ist ein Subsystem (wie `pipeline/`/
  `backtesting/`), in `quality_check.py` nur der Zyklenprüfung unterworfen. Die
  Kennzahlgruppen sind **Registry-Plugins** (`statistics_model`,
  `performance_model`) – neue nur über `engines/paper_trading_registry.py`.
- **Immutabilität:** Ergebnis-/Snapshot-Typen (`models/paper_trading.py`) sind
  `frozen`; Positionen werden über `dataclasses.replace` fortgeschrieben. Das
  **Portfolio** und das **Journal** sind bewusst zustandsbehaftete Manager
  (analog zu Engines/Caches), keine „Ergebnisobjekte".
- **Order-Management:** `OPEN/CLOSE/CANCEL/EXPIRE`; gültig nur auf einer offenen
  Position. **Validierung:** keine doppelte Position derselben Empfehlung, keine
  negative Größe, keine ungültigen Preise/Zeitstempel, keine ungültigen
  Statuswechsel (`PaperTradingValidationError`).
- **Risiko/Fractional Shares** kommen aus der Risk Engine bzw. `settings.toml`;
  Parameter aus `knowledge/paper_trading_rules.toml`. Trailing Stop **vorbereitet**.
  Details: `docs/PAPER_TRADING.md`.

## Trading Intelligence & Analytics Framework (umgesetzt in Sprint 12)

Das Analytics-Subsystem (`analytics/`) **liest** ausschließlich bestehende
`BacktestReport`/`PaperTradingReport` und erzeugt daraus objektive,
reproduzierbare Statistiken. Es **bewertet keine** Trades, verändert **keine**
Ergebnisse, erzeugt **keine** Empfehlungen und enthält **keine** ML.

```
BacktestReport + PaperTradingReport
        │
Normalisierung (Trades → AnalyticsTrade; Dimensionen aus recommendation_id/reasons)
        │
AnalyticsEngine (+ Registry/Cache) → zehn unabhängige Analysemodelle
        │
AnalyticsReport (AnalyticsResult, dashboard-fertig)
```

- **Schicht-Einordnung:** `analytics/` ist ein Subsystem (wie `pipeline/`/
  `backtesting/`/`paper_trading/`), in `quality_check.py` nur der Zyklenprüfung
  unterworfen. Die zehn Analysen sind **Registry-Plugins** und **unabhängig**
  voneinander (kein Modell importiert ein anderes; gemeinsame Bausteine in
  `aggregation.py`). Neue Modelle nur über `engines/analytics_registry.py`; die
  Engine bleibt **unverändert** (Open/Closed).
- **Immutabilität:** alle Ergebnistypen (`models/analytics.py`) sind `frozen`.
- **Transparenz:** jede Kennzahl entsteht aus `aggregation.py` (eine Quelle der
  Definitionen); abgeleitete Dimensionen (Strategie/Risiko/Score) sind aus
  `recommendation_id`/`reasons` nachvollziehbar; keine Blackbox, reproduzierbar.
- **Validierung:** leere Reports, fehlende Trades, nicht registrierte Modelle,
  ungültige Parameter. **Erweiterbarkeit:** Pattern-/Markt-Dimensionen sind
  label-basiert (Trade-Metadata) und ohne Engine-Änderung erweiterbar.
  Details: `docs/ANALYTICS.md`.

## AlphaAI Command Center / Dashboard (umgesetzt in Sprint 13)

Das Dashboard-Subsystem (`dashboard/`) ist **ausschließlich** die Presentation
Layer. Es **liest** die bestehenden Reports und **zeigt** sie an; es **berechnet
niemals** Daten, enthält **keinerlei** Geschäftslogik und erzeugt **keine**
Kennzahlen. Fehlt ein Wert, wird nur ein Platzhalter angezeigt.

```
Reports (ReportBundle)
        │
DashboardEngine → build_view_model()  (liest Reports ab, rechnet nichts)
        │
Widgets (Registry) → WidgetSpec  +  Router (Seiten) + Responsive (Gerät)
        │
DashboardView → render.py / app.py (einzige Streamlit-Schicht)
```

- **Schicht-Einordnung:** `dashboard/` ist ein Subsystem (wie `analytics/`), in
  `quality_check.py` nur der Zyklenprüfung unterworfen; `models/dashboard.py`
  gehört zur Entities-Schicht und importiert nur `models.analytics`. Die
  Streamlit-Schicht (`render.py`/`app.py`) ist die **einzige** Stelle mit
  Streamlit-Import (lazy) – die gesamte übrige Logik ist Streamlit-frei/testbar.
- **Open/Closed:** die 26 Widgets sind **Registry-Plugins** und **unabhängig**
  voneinander (kein Widget importiert ein anderes; gemeinsame Bausteine in
  `widgets/common.py`). Neue Widgets nur über `widget_registry.py`, neue Seiten
  nur über `router.py`, das Aussehen nur über `theme.py`. Die
  **`DashboardEngine` bleibt dafür unverändert**.
- **Immutabilität:** alle Anzeigetypen (`models/dashboard.py`) sind `frozen`; der
  veränderliche `DashboardState` sichert sich per `snapshot()`/`restore()`.
- **Robustheit:** Lade-/Fehlerzustände werden als Anzeige dargestellt; ein Fehler
  eines einzelnen Widgets wird isoliert (Platzhalter) – **keine Exceptions im
  Frontend**. **Keine Handelsparameter**, keine Broker-API. Details:
  `docs/DASHBOARD.md`.

## Aktueller Stand

Sprint 1–13 sind abgeschlossen (Fundament, Data Layer, Scanner Core, Indicator
Engine, Pattern Engine, Strategy Engine, Score Engine, Architecture Consolidation
mit Tag `v0.1.0-foundation`, Risk Engine, Recommendation Engine, End-to-End-
Integration & Validierung, Historical Backtesting Framework, Paper Trading
Framework, Trading Intelligence & Analytics Framework, AlphaAI Command Center /
Dashboard). Das Dashboard ist **rein darstellend** und **berechnet nichts**. Es
gibt bewusst weiterhin **keine Broker-API, keine automatische Orderausführung und
keine echten Orders** (Backtesting und Paper Trading simulieren ausschließlich;
Analytics wertet nur aus, das Dashboard zeigt nur an). Offene fachliche
Kalibrierung ist im `docs/VALIDATION_REPORT.md` dokumentiert.
