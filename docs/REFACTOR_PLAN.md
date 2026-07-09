# Refactoring-Plan – AlphaAI

**Stand:** 2026-07-09 · **Charakter:** Plan, **noch nicht umgesetzt.**
Grundlage: [`ARCHITECTURE_REVIEW.md`](ARCHITECTURE_REVIEW.md) und
[`TECH_DEBT.md`](TECH_DEBT.md). Finding-IDs (`TD-xx`) verweisen dorthin.

> Dieser Plan ändert **keinen** Code. Er beschreibt eine sichere Reihenfolge,
> um die technische Schuld abzubauen, **bevor** weitere Fachschichten (Risk,
> Recommendation, Dashboard, Persistenz) aufgesetzt werden.

## Leitprinzipien

1. **Verhaltenserhaltend.** Jeder Schritt ist ein reiner Umbau ohne Änderung
   der berechneten Ergebnisse. Die 307 bestehenden Tests sind das Sicherheitsnetz.
2. **Grün bleiben.** Nach jedem Teilschritt: `pytest`, `ruff`, `black` und der
   Qualitäts-Check (0 Zyklen / 0 Unabhängigkeitsverstöße) müssen bestehen.
3. **Klein und abgrenzbar.** Ein Commit = ein Finding (oder ein klar
   abgegrenzter Teil davon). Übergangsweise Aliasse statt „Big-Bang".
4. **Feature vor Fundament trennen.** TD-10 (Scanner-Verdrahtung) und TD-11
   (Multi-Timeframe) sind **eigene Feature-Sprints**, kein Aufräum-Refactor, und
   stehen deshalb am Ende bzw. außerhalb dieses Plans.

---

## Phase 0 – Absicherung (½ Tag)

Ziel: Refactoring risikofrei machen, bevor Strukturen bewegt werden.

- **P0.1** Qualitäts-Check als versioniertes Skript ins Repo aufnehmen
  (`scripts/quality_check.py`) und in die CI/Testsuite einhängen, damit
  Zyklenfreiheit und Plugin-Unabhängigkeit **automatisch** geprüft werden.
- **P0.2** Coverage-Schwelle festschreiben (z. B. „darf nicht unter 95 % fallen").
- **Ergebnis:** Jede folgende Phase hat ein hartes, automatisches Netz.

## Phase 1 – Domänenmodell konsolidieren *(TD-03, TD-05)*

Priorität **Hoch**. Adressiert den einzigen echten Clean-Architecture-Befund.
Aufwand: **M** (ca. 1–2 Tage).

- **P1.1** Neues Zielbild: `models/` wird die Entities-Schicht (importiert
  nichts aus höheren Schichten).
- **P1.2** Verschiebe reine Datencontainer nach `models/`:
  Enums (`MarketStatus`, `PatternType`, `PatternDirection`, `StrategyDirection`),
  Result/Report/Output-Dataclasses (`MarketResult`, `IndicatorOutput`,
  `IndicatorResult`, `PatternResult`, `PatternReport`, `StrategyResult`,
  `StrategyReport`, `ScoreResult`, `ScoreReport`, `ComponentScore`,
  `StructureBreak`).
- **P1.3** In `engines/*` und `*/base.py` nur noch **Re-Exports** belassen
  (Alias-Importe), damit bestehende Importpfade unverändert funktionieren.
- **P1.4** `strategies/base.py` und `scores/base.py`: `TYPE_CHECKING`-Importe von
  `engines` durch echte Importe aus `models` ersetzen (TD-05 löst sich auf).
- **P1.5** Nach Stabilisierung die Aliasse entfernen und Importe projektweit auf
  `models/` umstellen (separater Commit).
- **Guard:** Reine Verschiebung; `pytest`/Zyklencheck nach jedem Teilschritt.
  Erwartung: 0 Zyklen bleiben, da `models/` blattnah ist.

## Phase 2 – Generik gegen Duplikate *(TD-01, TD-02, TD-04)*

Priorität **Mittel**, Aufwand je **S**. Höchster Nutzen pro Aufwand.

- **P2.1 (TD-04)** Parameterfehler auf gemeinsame Wurzel heben:
  `class *ParameterError(AlphaAIError, ValueError)`. Bestehende
  `except ValueError`-Erwartungen bleiben gültig, `except AlphaAIError` fängt nun
  alles.
- **P2.2 (TD-01)** Generischen `Cache[T]` (FIFO, optional TTL) in `core/`
  einführen; die vier Engine-Caches und `data/cache.py` als dünne
  Spezialisierungen/Aliasse. Öffentliche API (hits/misses/get/set/clear)
  unverändert.
- **P2.3 (TD-02)** Generische `Registry[T]` in `core/`; die vier konkreten
  Registries erben und liefern nur noch `build_default_registry()`.
- **Guard:** Cache-/Registry-/Fehler-Tests je Familie bleiben unverändert grün.

## Phase 3 – Kleinere Smells & Konsistenz *(TD-07, TD-08, TD-15, TD-16, TD-17)*

Priorität **Niedrig**, Aufwand je **S**. „Aufräumen im Vorbeigehen".

- **P3.1 (TD-07)** Generischer `load_rules(path, section)`-Helfer in `core/`; die
  vier Loader parametrisieren ihn.
- **P3.2 (TD-08)** `require_int/float/bool` nach `core/` (mit übergebbarer
  Fehlerklasse). `*/base.py` importiert aus `core`.
- **P3.3 (TD-17)** Cache-Treffer ohne Mutation des geteilten Objekts
  signalisieren (Flag am Aufrufer bzw. flache Kopie der Metadaten).
- **P3.4 (TD-15)** Score-Loader gegen Registry prüfen und unbekannte Sektionen
  als klare Warnung melden; Doku-Hinweis (ADR-020) ergänzen.
- **P3.5 (TD-16)** Optionales `[logging].level` in `settings.toml`; `setup_logging`
  liest es.
- **Guard:** Bestehende Tests + je ein neuer Mini-Test pro Verhaltenszusatz.

## Phase 4 – Strukturschnitt `engines/` *(TD-06)*

Priorität **Niedrig**, Aufwand **M**. Rein organisatorisch; bewusst nach den
inhaltlichen Umbauten, um Merge-Konflikte zu minimieren.

- **P4.1** Unterpakete `engines/indicator/`, `engines/pattern/`,
  `engines/strategy/`, `engines/score/` (je `engine`/`registry`/`cache`).
- **P4.2** Übergangsweise Re-Exports in `engines/__init__` für alte Pfade.
- **Guard:** Nur Importpfade betroffen; Zyklencheck + Tests.

## Phase 5 – Performance & Speicher *(TD-12, TD-13, TD-09)*

Priorität **Mittel**, Aufwand **M–L**. Erst relevant, wenn große Universen real
gescannt werden; frühzeitig einplanen, weil es die Datenmodelle berührt.

- **P5.1 (TD-13)** Swing-/Sweep-Erkennung vektorisieren (rolling-Fenster/`numpy`),
  Ergebnisgleichheit gegen die bestehenden deterministischen Muster-Tests
  absichern.
- **P5.2 (TD-12)** Optionales „Slim/Trim" für Ergebnisobjekte (nur benötigte
  Fenster/letzte Werte); Cache-Kapazität/TTL konfigurierbar.
- **P5.3 (TD-09)** Optionale Parallelisierung der `*_all`- und
  `ScannerManager.scan_all`-Läufe über einen Executor, gesteuert durch
  `max_workers` aus der Config. Determinismus/Reihenfolge testgesichert
  (Ergebnisgleichheit sequenziell ↔ parallel).
- **Guard:** Vorher/Nachher-Messung; funktionale Gleichheit erzwingen.

## Phase 6 – Feature-Sprints (außerhalb des reinen Refactorings)

Keine Aufräumarbeiten, sondern neue Fähigkeiten – hier nur zur Einordnung:

- **F-A (TD-10)** Analyse-Orchestrator, der je Symbol die Engines aufruft und die
  vorbereiteten `ScanResult`-Felder füllt (End-to-End-Kette über den Scanner).
- **F-B (TD-11)** Multi-Timeframe-Aggregator, der die Engines je Zeitebene
  aufruft und zusammenführt.
- **F-C (TD-14/TD-18)** Optionale, leichte Config-Schema-Prüfung und klare
  Trennung Tuning-Parameter (TOML) vs. Algorithmus-Konstanten (Code).

---

## Sequenz & Aufwandsschätzung

| Phase | Findings | Nutzen | Aufwand | Risiko |
|---|---|---|:---:|:---:|
| 0 | Absicherung | Netz für alles Weitere | S | sehr niedrig |
| 1 | TD-03, TD-05 | Clean-Architecture-Kern | M | niedrig (Verschiebung) |
| 2 | TD-01, TD-02, TD-04 | −500 Zeilen Duplikat, klare Fehler | S×3 | niedrig |
| 3 | TD-07/08/15/16/17 | Konsistenz | S×5 | sehr niedrig |
| 4 | TD-06 | Navigierbarkeit | M | niedrig |
| 5 | TD-12/13/09 | Skalierung | M–L | mittel (Messen!) |
| 6 | TD-10/11/14/18 | neue Features | L | – (eigene Sprints) |

**Empfehlung:** Ein **Konsolidierungssprint** mit Phasen 0–2 (ca. 2–3 Tage)
bringt den größten strukturellen Gewinn bei geringstem Risiko. Phasen 3–4 sind
Feinschliff und können nebenläufig erfolgen. Phase 5 zeitlich an den ersten
großflächigen Universum-Scan koppeln. Phase 6 sind reguläre Feature-Sprints.

## Definition of Done je Phase

- `pytest` grün, Abdeckung ≥ 95 %.
- `ruff` und `black` ohne Beanstandung.
- Qualitäts-Check: 0 Import-Zyklen, 0 Unabhängigkeitsverstöße, 0 SOLID-Verstöße.
- Betroffene Findings in `TECH_DEBT.md` als erledigt markiert; `CHANGELOG.md`,
  `DECISIONS.md` (neue ADRs bei Strukturentscheidungen) und `HANDOVER.md`
  aktualisiert.
