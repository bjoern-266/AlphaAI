# Technische Schuld – AlphaAI

**Stand:** 2026-07-09 (nach Sprint 7; Teilumsetzung in Sprint 7.5)
**Charakter:** Bestandsaufnahme. Der geordnete Umbau steht in
[`REFACTOR_PLAN.md`](REFACTOR_PLAN.md); die Gesamtbewertung in
[`ARCHITECTURE_REVIEW.md`](ARCHITECTURE_REVIEW.md).

> **In Sprint 7.5 erledigt (verhaltenserhaltend):**
> **TD-03** (Domänentypen nach `models/` verschoben, alte Pfade als
> Re-Exports), **TD-05** (`strategies`/`scores` importieren nichts mehr aus
> `engines`), **TD-01** (generischer `Cache[T]` in `core/`), **TD-02**
> (generische `Registry[T]` in `core/`), **TD-04** (einheitliche
> `AlphaAIError`-Hierarchie, keine blanken `ValueError`/`KeyError` für
> Fachfehler). Zusätzlich: alle Ergebnisobjekte sind jetzt unveränderlich
> (`frozen`); `scripts/quality_check.py` prüft die Architektur automatisch.

**Legende**
Priorität: **Hoch** / Mittel / Niedrig · Aufwand: **S** (< ½ Tag) /
**M** (½–2 Tage) / **L** (> 2 Tage).
Kategorie: `arch` (Architektur), `smell` (Code Smell), `dup` (Duplikat),
`solid`, `perf`, `mem`, `feat` (Reifelücke).

---

## TD-03 · Domänentypen in `engines/` statt in der Entities-Schicht `models/`
- **Kategorie:** arch, Clean Architecture · **Priorität:** Hoch · **Aufwand:** M
- **Problem:** Die vorgesehene Entities-Schicht `models/` ist leer. Die
  Domänen-/Ergebnistypen sind stattdessen verstreut:
  `IndicatorResult`, `PatternReport`, `StrategyReport`, `ScoreReport`,
  `ScoreResult` liegen in `engines/`; `IndicatorOutput`, `PatternResult`,
  `StrategyResult` liegen in `<paket>/base.py` (bewusst, um Zyklen zu meiden).
  `ScoreResult` liegt abweichend in `engines/score_result.py` – inkonsistent zu
  `PatternResult`/`StrategyResult`.
- **Auswirkung:** Die stabilste Schicht (Entities) wird nicht genutzt; die
  Abhängigkeitsrichtung wird unscharf (siehe TD-05); Uneinheitlichkeit
  erschwert Navigation und Onboarding. Mit jeder weiteren Engine (Risk,
  Recommendation) wächst die Streuung.
- **Empfehlung:** Reine Datencontainer (Result/Report/Output-Dataclasses,
  Enums, `ComponentScore`, `StructureBreak`) schrittweise nach `models/`
  verschieben. `engines/` behält nur Verhalten (Engines, Registries, Loader).
  `*/base.py` importiert die Typen dann aus `models/` – zyklenfrei, da `models/`
  nichts importiert.
- **Guard:** Reine Verschiebung + Re-Export; bestehende Importpfade übergangsweise
  als Alias erhalten. 307 Tests als Netz.

## TD-01 · Cache 5× dupliziert (fehlende Generik)
- **Kategorie:** dup, solid (DRY/SRP) · **Priorität:** Mittel · **Aufwand:** S
- **Problem:** `engines/{indicator,pattern,strategy,score}_cache.py` sind
  nahezu identische FIFO-Caches (~52 Zeilen je Datei), dazu `data/cache.py`
  (TTL-Variante). Insgesamt ~5 Implementierungen desselben Konzepts.
- **Auswirkung:** ~200 Zeilen Redundanz; Fehlerkorrekturen/Verbesserungen müssen
  fünffach nachgezogen werden; Testduplikation.
- **Empfehlung:** Ein generischer `LruCache[T]` (oder `FifoCache[T]`) in `core/`
  (oder `data/`), typisiert über `Generic[T]`. Die vier Engine-Caches werden zu
  dünnen Aliassen. Die TTL-Variante bleibt eine Spezialisierung derselben Basis.
- **Guard:** Verhalten (hits/misses/Verdrängung) ist bereits testabgedeckt.

## TD-02 · Registry 4× dupliziert (fehlende Generik)
- **Kategorie:** dup, solid · **Priorität:** Mittel · **Aufwand:** S
- **Problem:** `engines/{indicator,pattern,strategy,score}_registry.py` bieten
  identische `register/get/__contains__/names/__len__`-Logik über
  unterschiedliche Elementtypen.
- **Auswirkung:** ~320 Zeilen Redundanz; Inkonsistenzrisiko bei künftigen
  Änderungen (z. B. Alias-Unterstützung, Deaktivierung).
- **Empfehlung:** Generische `Registry[T]`-Basis in `core/`; die vier konkreten
  Registries erben und ergänzen nur `build_default_registry()`.
- **Guard:** Registry-Tests je Familie bleiben unverändert gültig.

## TD-04 · Zwei Exception-Wurzeln
- **Kategorie:** smell, Fehlerbehandlung · **Priorität:** Mittel · **Aufwand:** S
- **Problem:** `ConfigError`, `IndicatorRulesError`, `PatternRulesError`,
  `StrategyRulesError`, `ScoreRulesError` erben von `AlphaAIError`. Die
  Parameterfehler `IndicatorParameterError`, `PatternParameterError`,
  `StrategyParameterError`, `ScoreParameterError` erben dagegen von `ValueError`.
- **Auswirkung:** Aufrufer können nicht mit einem `except AlphaAIError` alle
  fachlichen Fehler abfangen; die Fehlerhierarchie ist uneinheitlich.
- **Empfehlung:** Gemeinsame Basis `AlphaAIError` auch für die Parameterfehler
  (ggf. Mehrfachvererbung `class ...ParameterError(AlphaAIError, ValueError)`,
  damit bestehende `except ValueError`-Erwartungen erhalten bleiben).
- **Guard:** Tests prüfen die konkreten Fehlerklassen – bleiben grün.

## TD-05 · `strategies`/`scores` an Engine-Result-Typen gekoppelt
- **Kategorie:** arch, Dependency Rules · **Priorität:** Mittel · **Aufwand:** M
- **Problem:** `strategies/base.py` und `scores/base.py` importieren
  `IndicatorResult`/`PatternReport` aus `engines` unter `TYPE_CHECKING` und
  nutzen sie zur Laufzeit per Duck-Typing.
- **Auswirkung:** Die konzeptionelle Abhängigkeitsrichtung („Fachlogik nutzt
  Engine-Ausgaben") ist real vorhanden, aber nur schwach typisiert; statische
  Prüfung ist eingeschränkt. Symptom von TD-03.
- **Empfehlung:** Nach Umsetzung von TD-03 zeigen `strategies`/`scores` sauber
  auf `models/` statt auf `engines/`. Der `TYPE_CHECKING`-Umweg entfällt.
- **Guard:** Ergibt sich automatisch aus TD-03.

## TD-09 · Keine Parallelisierung; `max_workers` ungenutzt
- **Kategorie:** perf, feat · **Priorität:** Mittel · **Aufwand:** M
- **Problem:** `ScannerManager.scan_all` und `*_all`-Methoden (Indicator/Pattern
  /Score) verarbeiten Symbole strikt sequenziell. `ScanRequest.max_workers` ist
  deklariert, aber wirkungslos.
- **Auswirkung:** Bei großen Universen (S&P 500 ≈ 500, Russell 2000 ≈ 2000
  Symbole) steigt die Laufzeit linear; Netz-/Rechenzeit wird nicht überlappt.
- **Empfehlung:** Da Engines seiteneffektfrei je Symbol arbeiten, ist die
  Verarbeitung „embarrassingly parallel". Einführung eines optionalen
  Executors (Thread- für I/O-lastige Provider, Prozess-Pool für Rechenlast),
  gesteuert über `max_workers` aus der Config. Reihenfolge- und
  Determinismus-Garantien beibehalten.
- **Guard:** Ergebnisgleichheit sequenziell vs. parallel testen.

## TD-10 · Scanner nicht mit den Engines verdrahtet
- **Kategorie:** arch, feat · **Priorität:** Mittel · **Aufwand:** M
- **Problem:** `ScanResult` besitzt vorbereitete Felder
  (`indicators`, `patterns`, `score`, …), doch die `ScanPipeline` befüllt nur
  die Rohdaten. Die Kette Indicator→Pattern→Strategy→Score wird aktuell nur in
  Smoke-Tests manuell verdrahtet.
- **Auswirkung:** Es gibt noch keinen End-to-End-Lauf „Universum → bewertete
  Setups" über den Scanner. Integrationsrisiko wächst, je später verdrahtet wird.
- **Empfehlung:** Einen dedizierten Analyse-Schritt/Orchestrator einführen, der
  je Symbol die Engines aufruft und die vorbereiteten `ScanResult`-Felder füllt
  – strikt über die bestehenden Engine-Schnittstellen (keine neue Kopplung).
  Bewusst als eigener Sprint einzuplanen (kein Review-Refactor).
- **Guard:** Neue Integrationstests entlang der Kette.

## TD-12 · Speicher: volle DataFrames/Serien in Ergebnissen und Caches
- **Kategorie:** mem, perf · **Priorität:** Mittel · **Aufwand:** M
- **Problem:** `MarketResult`/`ScanResult` halten komplette OHLCV-DataFrames;
  `IndicatorResult` speichert je Indikator die **vollständige** Zeitreihe je
  Komponente. Caches (FIFO, Default-Kapazität 128) legen diese schweren Objekte
  ab.
- **Auswirkung:** Bei breiten Universen × Timeframes wächst der
  Speicherverbrauch schnell (Serien × Symbole × Cache-Einträge). Für Scanner,
  die überwiegend die letzten Werte brauchen, ist das teuer.
- **Empfehlung:** (a) Cache-Kapazität/TTL konfigurierbar und pro Kontext
  wählbar; (b) optionales „Trimming" – Ergebnisse können auf benötigte Fenster/
  letzte Werte reduziert werden; (c) Erwägung eines Lazy-/Slim-Modus für
  `IndicatorResult` (nur `latest` + optionale Serien).
- **Guard:** Messung vorher/nachher; Verhalten der Konsumenten unverändert.

## TD-06 · `engines/` als überladenes „God-Package"
- **Kategorie:** smell, Wartbarkeit · **Priorität:** Niedrig · **Aufwand:** M
- **Problem:** 17 Dateien für vier fachlich getrennte Engines liegen flach in
  `engines/`, unterschieden nur per Namenspräfix (`indicator_*`, `pattern_*`, …).
- **Auswirkung:** Navigation/Übersicht leidet; das Präfix ersetzt eine
  Paketstruktur.
- **Empfehlung:** Unterpakete `engines/indicator/`, `engines/pattern/`,
  `engines/strategy/`, `engines/score/` (je engine/registry/cache/result). Rein
  strukturell, keine Verhaltensänderung.
- **Guard:** Nur Importpfade betroffen; Aliasse während der Migration.

## TD-07 · Rules-Loader 4× dupliziert
- **Kategorie:** dup · **Priorität:** Niedrig · **Aufwand:** S
- **Problem:** `load_indicator_rules`, `load_pattern_rules`,
  `load_strategy_rules`, `load_score_rules` teilen dasselbe Muster (TOML lesen,
  `TOMLDecodeError` → Fehler, Sektion prüfen, Version aus `[meta]`).
- **Auswirkung:** Redundanz; jede Verbesserung (z. B. Schema-Prüfung) vierfach.
- **Empfehlung:** Generische Hilfsfunktion `load_rules(path, section, ...)` in
  `core/`; die konkreten Loader parametrisieren sie.
- **Guard:** Bestehende Loader-Tests bleiben gültig.

## TD-08 · `require_int/float/bool` mehrfach dupliziert
- **Kategorie:** dup · **Priorität:** Niedrig · **Aufwand:** S
- **Problem:** Parameter-Helfer existieren nahezu identisch in
  `indicators/base.py`, `patterns/base.py`, `strategies/base.py`,
  `scores/base.py` (nur unterschiedliche Fehlerklasse).
- **Auswirkung:** Redundanz; leicht divergierende Validierungsregeln möglich.
- **Empfehlung:** Gemeinsame Helfer in `core/` (mit übergebbarer Fehlerklasse).
  **Abwägung:** bewusst duplizieren wurde als Preis für Paket-Unabhängigkeit
  gewählt (ADR-Kontext). Konsolidierung nur, wenn `core` als erlaubte
  Basisschicht akzeptiert ist (ist es).
- **Guard:** Verhaltensgleichheit über bestehende Parameter-Fehlertests.

## TD-11 · Multi-Timeframe nur vorbereitet
- **Kategorie:** feat · **Priorität:** Niedrig · **Aufwand:** M
- **Problem:** Engines führen ein `timeframe`-Label in Metadaten, aber es gibt
  keinen Aggregator, der mehrere Zeitebenen kombiniert.
- **Auswirkung:** MTF-Setups (z. B. Tagestrend + Stunden-Trigger) sind noch
  nicht möglich; die „Vorbereitung" ist bislang nur ein Label.
- **Empfehlung:** Eigener MTF-Orchestrator in einem späteren Sprint, der die
  Engines je Zeitebene aufruft und Ergebnisse zusammenführt. Kein Review-Thema.
- **Guard:** Bei Umsetzung neue MTF-Tests.

## TD-13 · Swing-/Sweep-Erkennung mit Python-Schleifen
- **Kategorie:** perf · **Priorität:** Niedrig · **Aufwand:** M
- **Problem:** `swing_highs/lows` prüfen je Kerze mit `all(...)`-Generatoren
  (O(n·lookback)); `liquidity_sweep` scannt je Pivot nachfolgende Kerzen
  (worst case O(pivots·n)).
- **Auswirkung:** Bei langen Historien/vielen Symbolen messbare Rechenzeit; die
  restlichen Indikatoren sind bereits vektorisiert.
- **Empfehlung:** Vektorisierung via rolling-Fenster/`numpy` (z. B.
  `rolling(2k+1).max()`-Vergleich für Pivots). Ergebnisgleichheit sicherstellen.
- **Guard:** Bestehende deterministische Muster-Tests als Referenz.

## TD-14 · Config auf zwei Orte verteilt, kein Schema
- **Kategorie:** smell, Config · **Priorität:** Niedrig · **Aufwand:** M
- **Problem:** Einstellungen in `config/` (`settings.toml`, `universe.toml`),
  Regeln in `knowledge/` (`*_rules.toml`). Validierung erfolgt handkodiert; es
  gibt kein deklaratives Schema.
- **Auswirkung:** Zwei Orte erhöhen die Einstiegshürde; manuelle Validierung ist
  fehleranfälliger und wird pro Loader wiederholt (siehe TD-07).
- **Empfehlung:** Ablageorte dokumentiert klar trennen (Settings vs.
  Fachregeln – bewusst!) und mittelfristig eine leichte Schema-Prüfung
  einführen (weiterhin ohne schwere Abhängigkeit; z. B. zentrale
  Validierungshelfer). Kein Zwang zu Pydantic.
- **Guard:** Config-Tests bestehen.

## TD-15 · Score-Sektionsname muss Modellname entsprechen
- **Kategorie:** smell · **Priorität:** Niedrig · **Aufwand:** S
- **Problem:** In `score_rules.toml` muss der Sektionsname exakt dem
  registrierten Modellnamen entsprechen (`[weighted_score]` ↔ `weighted_score`).
  Eine Abweichung führt still zu „Modell nicht registriert" (nur Warnung).
- **Auswirkung:** Verkonfiguration wird leicht übersehen (kein harter Fehler).
- **Empfehlung:** Beim Laden optional gegen die Registry prüfen und unbekannte
  Sektionen als **Warnung mit Klartext** melden (bereits teilweise vorhanden);
  in der Doku explizit festhalten (ADR-020 verweisen).
- **Guard:** Ein Test, der eine unbekannte Sektion → Warnung erwartet.

## TD-16 · Log-Level nicht aus Config
- **Kategorie:** smell, Logging · **Priorität:** Niedrig · **Aufwand:** S
- **Problem:** `setup_logging(level=...)` nimmt das Level als Argument, aber es
  wird nicht aus `settings.toml` gespeist; Engines loggen zudem sparsam.
- **Auswirkung:** Betriebseinstellung (Verbosity) ist nicht datengetrieben;
  Diagnose im Feld erschwert.
- **Empfehlung:** Optionales `[logging].level` in `settings.toml`; ausgewählte
  Engine-Meilensteine auf `debug` mitloggen.
- **Guard:** Logging-Tests bleiben gültig (idempotenz).

## TD-17 · `cache_hit` per Mutation des gecachten Objekts
- **Kategorie:** smell · **Priorität:** Niedrig · **Aufwand:** S
- **Problem:** `MarketRepository` setzt `cached.metadata['cache_hit'] = True` auf
  dem **gecachten** `MarketResult` und mutiert damit ein geteiltes Objekt.
- **Auswirkung:** Subtiler Seiteneffekt; das Flag „klebt" am geteilten Objekt.
  Für die aktuelle Nutzung unkritisch, aber überraschend.
- **Empfehlung:** Cache-Treffer als separate, nicht-mutierende Information
  zurückgeben (z. B. flache Kopie der Metadaten oder Rückgabewert am Aufrufer).
- **Guard:** Repository-/Pipeline-Cache-Tests.

## TD-18 · Scoring-/Strength-Konstanten im Code statt in TOML
- **Kategorie:** smell, Config · **Priorität:** Niedrig · **Aufwand:** M
- **Problem:** Beschreibende Skalierungskonstanten (z. B.
  `_FULL_SCALE_RATIO`, Confidence-Zuordnungen in FVG/BOS, Komponenten-Formeln in
  `scores/base.py`) sind dokumentiert, liegen aber im Code – abweichend vom
  Grundsatz „keine Hardcodes".
- **Auswirkung:** Feinjustierung erfordert Codeänderung; die Grenze zwischen
  „Algorithmus-Konstante" und „Tuning-Parameter" ist nicht überall scharf.
- **Empfehlung:** Klare Linie ziehen und dokumentieren: echte Tuning-Größen in
  TOML, reine Algorithmus-Konstanten im Code (bereits per ADR begründet).
  Wo sinnvoll, einzelne Skalen in die jeweiligen `*_rules.toml` heben.
- **Guard:** Bestehende deterministische Tests; Werte unverändert lassen.

---

## Übersicht (sortiert nach Priorität, dann Aufwand)

| ID | Titel | Kat. | Prio | Aufw. |
|---|---|---|:---:|:---:|
| TD-03 | Domänentypen nach `models/` | arch | Hoch | M |
| TD-01 | Generischer Cache | dup | Mittel | S |
| TD-02 | Generische Registry | dup | Mittel | S |
| TD-04 | Einheitliche Exception-Wurzel | smell | Mittel | S |
| TD-05 | `strategies`/`scores` → `models/` | arch | Mittel | M |
| TD-09 | Parallelisierung | perf | Mittel | M |
| TD-10 | Scanner ↔ Engines verdrahten | arch | Mittel | M |
| TD-12 | Speicher/Cache-Trimming | mem | Mittel | M |
| TD-07 | Generischer Rules-Loader | dup | Niedrig | S |
| TD-08 | Parameter-Helfer in `core` | dup | Niedrig | S |
| TD-15 | Score-Sektion vs. Modellname | smell | Niedrig | S |
| TD-16 | Log-Level aus Config | smell | Niedrig | S |
| TD-17 | `cache_hit` ohne Mutation | smell | Niedrig | S |
| TD-06 | `engines/` in Unterpakete | smell | Niedrig | M |
| TD-11 | Multi-Timeframe-Aggregator | feat | Niedrig | M |
| TD-13 | Swing/Sweep vektorisieren | perf | Niedrig | M |
| TD-14 | Config-Schema/-Ablage | smell | Niedrig | M |
| TD-18 | Scoring-Konstanten klären | smell | Niedrig | M |

**Kein Finding ist ein Architekturbruch.** Alle sind isoliert, testgesichert
und ohne Verhaltensänderung umsetzbar.
