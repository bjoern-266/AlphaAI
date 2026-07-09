# Architecture Review – AlphaAI

**Rolle:** Principal Software Architect (unabhängiges Review)
**Datum:** 2026-07-09
**Umfang:** Gesamtprojekt nach Sprint 7 (Score Engine)
**Charakter:** Reine Analyse – **keine** Codeänderung, kein Refactoring.

Dieser Bericht bewertet den Ist-Zustand. Die Detailauflistung der Schwächen
steht in [`TECH_DEBT.md`](TECH_DEBT.md), der geordnete Umbauplan in
[`REFACTOR_PLAN.md`](REFACTOR_PLAN.md). Findings werden dort als `TD-xx`
referenziert.

---

## 1. Methodik

- Statische Analyse des Importgraphen (AST, 83 Module) auf Zyklen und
  Abhängigkeitsrichtung.
- Schicht- und Duplikatanalyse (LOC, Klassenfamilien).
- Prüfung gegen Clean Architecture, SOLID und die 20 geforderten Kriterien.
- Auswertung der Testabdeckung (`coverage`) und der Qualitätsheuristiken.

## 2. Kennzahlen (Ist-Zustand)

| Kennzahl | Wert |
|---|---|
| Produktivcode (ohne Tests) | ~6.500 Zeilen / 66 Module |
| Testcode | 3.831 Zeilen / 61 Dateien, **307 Tests** |
| Gesamt-Testabdeckung | **97 %** |
| Import-Zyklen | **0** (83 Module) |
| Plugin-Familien | 4 (Indikatoren, Muster, Strategien, Scores) |
| Registry-Klassen | 4 (nahezu identisch) |
| Cache-Klassen | 5 (1× TTL, 4× FIFO – nahezu identisch) |
| Leere Platzhalter-Pakete | 3 (`dashboard`, `database`, `models`) |
| Konfigurationsdateien (TOML) | 6 (`config/` + `knowledge/`) |

## 3. Gesamturteil

**Reifegrad: 7,6 / 10 – solide, produktionsnah, mit klar umrissener und
kontrollierbarer technischer Schuld.**

AlphaAI ist für ein System dieser Größe **überdurchschnittlich sauber**: strikt
geschichtet, zyklenfrei, durchgängig per Dependency Injection testbar (97 %
Abdeckung) und konsequent datengetrieben (TOML-Regeln + Registries). Die
Schwächen sind **struktureller, nicht funktionaler** Natur und größtenteils
kostengünstig zu beheben, bevor sie sich zementieren:

1. **Duplikation** durch fehlende Generik (Caches, Registries, Rules-Loader).
2. **Verstreute Domänentypen** bei leerer Entities-Schicht (`models/`).
3. **Fehlende Parallelisierung** und **nur vorbereitete Multi-Timeframe-Logik**
   – heute unkritisch, bei großen Universen (S&P 500, Russell 2000) aber ein
   Performance- und Speicherrisiko.

Keiner dieser Punkte ist ein Architekturbruch; alle sind in wenigen, klar
abgrenzbaren Umbauschritten adressierbar (siehe `REFACTOR_PLAN.md`).

## 4. Bewertung der 20 Prüfaspekte

| # | Aspekt | Score | Kurzbegründung |
|---|---|:---:|---|
| 1 | Clean Architecture | 7 | Saubere Schichten, Abhängigkeiten nach unten; **aber** Entities-Schicht (`models/`) leer, Domänentypen in `engines/`/`*/base.py` verstreut. |
| 2 | SOLID | 8 | SRP/OCP/DIP stark (Registries, DI, Base-Klassen); LSP eingehalten. Duplikation (Cache/Registry) verrät eine fehlende Abstraktion. |
| 3 | Dependency Rules | 8 | Ausschließlich nach unten, automatisch geprüft. Leichte Unschärfe: `strategies`/`scores` referenzieren Engine-Result-Typen (nur `TYPE_CHECKING`). |
| 4 | Import-Zyklen | 10 | 0 Zyklen über 83 Module, per CI-tauglichem Skript nachgewiesen. |
| 5 | Erweiterbarkeit | 9 | Neue Indikatoren/Muster/Strategien/Scores rein über Registry + TOML, ohne Engine-Änderung. |
| 6 | Wartbarkeit | 7 | Klare Struktur, hohe Abdeckung; gemindert durch Duplikation und das überladene `engines/`-Paket (17 Dateien). |
| 7 | Testbarkeit | 10 | DI überall (Uhr, Downloader, Timer, Registry, Cache), deterministisch, 97 %. Vorbildlich. |
| 8 | Performance | 6 | Ausreichend für kleine Universen; sequenzielle Verarbeitung und Python-Schleifen (Swing-Erkennung) skalieren nicht linear-günstig. |
| 9 | Speicherverbrauch | 6 | Ergebnisobjekte halten volle DataFrames/Serien; Caches speichern schwere Objekte ohne Trimming. |
| 10 | Multi-Timeframe | 5 | Nur vorbereitet (Timeframe-Label in Metadaten); kein Aggregator, keine echte MTF-Logik. |
| 11 | Parallelisierung | 4 | Ausschließlich sequenziell; `max_workers` deklariert, aber ungenutzt; `*_all`-Methoden nicht parallelisiert. |
| 12 | Plugin-Fähigkeit | 9 | Vier saubere Plugin-Familien (Base + Registry + TOML). Sehr gut. |
| 13 | Datenmodell | 6 | Kanonisches OHLCV-Schema exzellent; Result-Typen aber verstreut, keine zentrale Domäne, `models/` leer. |
| 14 | Registry-System | 8 | Funktional und getestet; 4× nahezu identisch (fehlende Generik). |
| 15 | Knowledge-System | 9 | TOML-Regeln + Markdown, KI-pflegbar, datengetrieben, versioniert. |
| 16 | Config-System | 7 | TOML-only und validiert; verteilt auf `config/` + `knowledge/`, manuelle Validierung, kein Schema, Loader-Duplikate. |
| 17 | Caching | 6 | Vorhanden und getestet; fünf Varianten (Duplikat), Engine-Caches ohne TTL, Speicherthema. |
| 18 | Fehlerbehandlung | 7 | Fail-Fast, isolierte Boundaries; **aber** zwei Exception-Wurzeln (`AlphaAIError` vs. `*ParameterError(ValueError)`). |
| 19 | Logging | 7 | Zentral, idempotent, rotierend; Log-Level nicht config-gesteuert, Engines loggen sparsam. |
| 20 | Dokumentation | 9 | Vorbildlich: 7 Docs + ADRs, nach jedem Sprint gepflegt. |

**Durchschnitt:** 7,45 → gerundetes Gesamturteil **7,6 / 10** (Testbarkeit und
Knowledge/Doku heben den funktionalen Reifegrad an).

## 5. Schichtenbewertung (0–10)

| Schicht | Score | Begründung |
|---|:---:|---|
| `core` | 9 | Minimal, DI-fähig, zentrale Pfade/Config/Logging sauber. Abzug: zwei Exception-Wurzeln, Log-Level nicht aus Config (TD-04, TD-16). |
| `config` | 8 | Reines TOML, validiert, keine Hardcodes. Abzug: zwei Ablageorte, manuelle Validierung, kein Schema (TD-14). |
| `providers` | 9 | Sauberes Provider-Muster, injizierbarer Download, vorbereitete Provider ehrlich (Fehler statt Dummy). Breiter `except` an der Quelle-Grenze (vertretbar). |
| `repositories` | 9 | Dünn, klar, DI. Abzug: `metadata['cache_hit']` per Mutation des gecachten Objekts (TD-17). |
| `data` | 8 | Kanonisches OHLCV, TTLCache, Validator solide. Abzug: `MarketResult` hält DataFrames (Speicher), TTLCache gehört zur Cache-Duplikatfamilie (TD-01, TD-12). |
| `scanner` | 8 | Saubere Orchestrierung, gute Statistik/Logs. Abzug: noch nicht mit den Engines verdrahtet, sequenziell, `max_workers` ungenutzt (TD-09, TD-10). |
| `engines` | 7 | 0 Zyklen, gut getestet. Abzug: „God-Package" mit 4 Engines flach (17 Dateien), starke Duplikation (Cache/Registry/Loader), Domänentypen hier beheimatet (TD-01/02/03/06/07). |
| `patterns` | 8 | Unabhängige Muster, gemeinsame Helfer sauber getrennt. Abzug: Swing-Erkennung O(n·lookback) in Python-Schleifen, Scoring-Konstanten im Code (TD-13, TD-18). |
| `strategies` | 8 | Unabhängige Strategien, deklarative Anforderungen. Abzug: Abhängigkeit auf Engine-Result-Typen via `TYPE_CHECKING` (TD-05). |
| `scores` | 8 | Unabhängige Modelle, transparente Komponenten. Abzug: `ScoreResult` liegt in `engines/` (nicht in `scores/base.py` wie bei Pattern/Strategy → Inkonsistenz, TD-03). |
| `knowledge` | 9 | Datengetrieben, versioniert, KI-pflegbar. Kleiner Foot-gun: Score-Sektionsname == Modellname (TD-15). |
| `dashboard` | 2 | Leerer Platzhalter (geplant). Score spiegelt den Ist-Zustand, nicht einen Defekt. |
| `database` | 2 | Leerer Platzhalter (geplant). Persistenz noch nicht umgesetzt. |
| `tests` | 9 | 307 Tests, 97 %, deterministisch, DI. Abzug: einzelne sehr lockere Asserts, Helfer-Duplikation. |

> `models/` ist als Schicht nicht separat bewertet, weil leer – genau das ist
> ein Kernbefund (TD-03): Die vorgesehene Entities-Schicht existiert, wird aber
> nicht genutzt, während Domänentypen in `engines/` und `*/base.py` liegen.

## 6. Stärken (bewahren)

- **Zyklenfreiheit als Prinzip**, per Skript nachweisbar – ideal für CI.
- **Plugin-Architektur** (Base + Registry + TOML) ist konsistent über vier
  Familien durchgezogen; Erweiterung ohne Engine-Änderung ist real belegt.
- **Testbarkeit** durch konsequente Dependency Injection (Uhr, Downloader,
  Timer). 97 % Abdeckung sind kein Zufall, sondern Folge des Designs.
- **Datengetriebene Regeln** (TOML) trennen Fachwissen sauber vom Code und
  erfüllen das Kernziel „keine Projektinformation nur im Chat".
- **Dokumentationsdisziplin** (ADRs, Handover, Changelog je Sprint).

## 7. Wichtigste Schwächen (Details in TECH_DEBT.md)

| ID | Schwäche | Priorität |
|---|---|:---:|
| TD-03 | Domänentypen in `engines/` statt in `models/`; Entities-Schicht leer | **Hoch** |
| TD-01 | Cache 5× dupliziert (fehlende Generik) | Mittel |
| TD-02 | Registry 4× dupliziert (fehlende Generik) | Mittel |
| TD-04 | Zwei Exception-Wurzeln (`AlphaAIError` vs. `ValueError`) | Mittel |
| TD-05 | `strategies`/`scores` an Engine-Result-Typen gekoppelt (`TYPE_CHECKING`) | Mittel |
| TD-09 | Keine Parallelisierung; `max_workers` ungenutzt | Mittel |
| TD-10 | Scanner nicht mit Engines verdrahtet (Integrationslücke) | Mittel |
| TD-12 | Speicher: volle DataFrames/Serien in Ergebnissen und Caches | Mittel |
| TD-06 | `engines/` als überladenes „God-Package" | Niedrig |
| TD-07 | Rules-Loader 4× dupliziert | Niedrig |
| TD-08 | `require_int/float/bool` 4× dupliziert | Niedrig |
| TD-11 | Multi-Timeframe nur vorbereitet, kein Aggregator | Niedrig |
| TD-13 | Swing-/Sweep-Erkennung mit Python-Schleifen (Performance) | Niedrig |
| TD-14 | Config auf zwei Orte verteilt, kein Schema | Niedrig |
| TD-15 | Score-Sektionsname == Modellname (implizite Kopplung) | Niedrig |
| TD-16 | Log-Level nicht aus Config | Niedrig |
| TD-17 | `cache_hit` per Mutation des gecachten Objekts | Niedrig |
| TD-18 | Scoring-/Strength-Konstanten im Code (nicht in TOML) | Niedrig |

## 8. Fazit

Die Architektur trägt. Sie ist erweiterbar, testbar und dokumentiert. Bevor
weitere Schichten (Risk, Recommendation, Dashboard, Persistenz) aufgesetzt
werden, empfiehlt sich ein **kurzer Konsolidierungssprint**, der vor allem
TD-03 (Domänenmodell), TD-01/TD-02 (Generik für Cache/Registry) und TD-04
(Exception-Wurzel) adressiert. Diese Punkte werden mit jeder weiteren Schicht
teurer. Alles Weitere ist Feinschliff. Der konkrete, risikoarme Weg dahin steht
in [`REFACTOR_PLAN.md`](REFACTOR_PLAN.md).
