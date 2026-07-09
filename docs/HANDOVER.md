# Handover (Übergabe)

_Diese Datei wird nach jedem Sprint automatisch aktualisiert._ Sie ermöglicht
es einer neuen Sitzung (Mensch oder KI), nahtlos weiterzuarbeiten – **ohne**
dass Wissen nur im Chat existiert.

## Stand der Übergabe

- **Datum:** 2026-07-09
- **Abgeschlossener Sprint:** Sprint 8 – Professional Risk Engine
- **Projektwurzel:** `AlphaAI/` (im Repository `AlphaAI` ist dies die Wurzel)
- **Branch:** `claude/alphaai-project-bootstrap-c51pse`
- **Tag:** `v0.1.0-foundation` (stabiler Fundament-Stand nach Sprint 7.5)

## So startet die nächste Sitzung

1. In das Projektverzeichnis wechseln: `cd AlphaAI`.
2. Umgebung einrichten: `python3.12 -m venv .venv && source .venv/bin/activate`.
3. Installieren: `pip install -e ".[dev]"`.
4. Fundament prüfen: `python -m scripts.check_setup`.
5. Tests ausführen: `pytest` (aktuell 413 Tests).
6. Architektur prüfen: `python scripts/quality_check.py` (muss BESTANDEN melden).

## Qualitätsprüfung Sprint 8 (Ergebnis)

Vor dem Commit automatisch geprüft:

| Prüfung | Ergebnis |
|---|---|
| Import-Zyklen | **0** |
| Entities-Schicht `models/` (kein Import aus höheren Schichten) | **0 Verstöße** |
| Plugin-Unabhängigkeit (inkl. Risk-Modelle) | **0 Verstöße** |
| SOLID-Heuristik (inkl. Risk) | **0 Verstöße** |
| Ergebnisobjekte unveränderlich (`frozen`) | **vollständig** |
| Ruff / Black | **konform** |
| pytest | **413 bestanden** |

## Risk Engine – Kurzüberblick für die Weiterarbeit

- Einstieg: `RiskEngine.from_config()` lädt `knowledge/risk_rules.toml` und
  `config/settings.toml` und registriert alle Standard-Modelle.
- Bewertung: `engine.assess(score_report, indicators, data=frame, symbol=...,
  open_positions=(...))` → `RiskReport` mit einem `RiskResult` je Score.
- Ergebnis: `report.results`; `report.highest_risk(n)` sortiert nach Risiko
  (reine Anzeige, **keine** Empfehlung). Jeder `RiskResult` trägt die zehn
  Komponenten in `risk_components`, alle Modellwerte in
  `metadata['model_values']` und erklärbare Beitragszeilen in `reasons`.
- **Neues Risk-Modell hinzufügen** (einziger erlaubter Weg):
  1. Datei in `risk/` anlegen, `BaseRiskModel` implementieren (`compute`),
     `component` auf einen Namen aus `RISK_COMPONENT_NAMES` setzen (oder `""`),
     nur `context`/`params` nutzen, kein anderes Modell importieren.
  2. In `engines/risk_registry.py::build_default_registry` registrieren.
  3. Abschnitt + ggf. Gewicht in `knowledge/risk_rules.toml` ergänzen. Die
     Engine muss dafür **nicht** geändert werden.
  4. Eigene Testdatei `tests/test_risk_<name>.py` anlegen.
- **Konto-/Depotwerte** kommen ausschließlich aus `settings.toml`, alle übrigen
  Parameter aus `risk_rules.toml`. Die Engine erzeugt **keine** Order.

## Architektur-Konsolidierung (Sprint 7.5) – für die Weiterarbeit

- **Datentypen** liegen in `models/` (`market`, `indicator`, `pattern`,
  `strategy`, `score`; `risk`/`recommendation` vorbereitet). Neue Datentypen
  dort anlegen. Alte Pfade (`data.market_result`, `engines.*_result`,
  `*/base.py`) re-exportieren weiterhin – bestehender Code bleibt gültig.
- **Ergebnisobjekte sind `frozen`.** Nichts nach der Erstellung mutieren; für
  Änderungen `dataclasses.replace(obj, feld=…)` verwenden. Engines sammeln in
  lokalen Listen/Dicts und konstruieren das Ergebnis **einmalig am Ende**.
- **Caches/Registries** erben von `core.cache.Cache[T]` bzw.
  `core.registry.Registry[T]`. **Fehler** immer aus `core.exceptions`
  (`AlphaAIError`-Hierarchie), nie blankes `ValueError`/`KeyError`.

## Score Engine – Kurzüberblick für die Weiterarbeit

- Einstieg: `ScoreEngine.from_config()` erzeugt eine Engine mit Gewichten aus
  `knowledge/score_rules.toml` und allen Standard-Modellen.
- Bewertung: `engine.score(strategy_report, indicators, patterns, symbol,
  timeframe)` → `ScoreReport` mit einem `ScoreResult` je Hypothese.
- Ergebnis: `report.results`; `report.top(n)` sortiert nach Gesamtscore (reine
  Anzeige, **keine** Empfehlung). Jeder `ScoreResult` trägt die acht
  Komponenten in `component_scores` und alle Modellwerte in
  `metadata['model_scores']`.
- **Neues Score-Modell hinzufügen** (einziger erlaubter Weg):
  1. Datei in `scores/` anlegen, `BaseScoreModel` implementieren (`compute`),
     nur Komponenten/Kontext nutzen, kein anderes Modell.
  2. In `engines/score_registry.py::build_default_registry` registrieren.
  3. Abschnitt in `knowledge/score_rules.toml` ergänzen (Sektionsname =
     Modellname). Die Engine muss dafür **nicht** geändert werden.
  4. Eigene Testdatei `tests/test_score_<name>.py` anlegen.
- Neue **Komponenten** kommen in `scores/base.py::compute_components` hinzu und
  werden in `COMPONENT_NAMES` sowie den Gewichten des Weighted Score ergänzt.

## Wichtige Konventionen (unbedingt einhalten)

- **Keine hartcodierten Werte** – Gewichte in `knowledge/*.toml`, Einstellungen
  in `config/*.toml`. Komponenten-Formeln sind dokumentierte Messungen.
- **Type Hints und Docstrings** für jede öffentliche Funktion/Klasse.
- **Black- und Ruff-konform** (Zeilenlänge 100).
- **Abhängigkeiten zeigen nur nach unten**; kein Score-Modell/Strategie/Muster/
  Indikator hängt von einem anderen ab.
- **Kein Auto-Trading**, keine Entscheidung/Positionsgröße/Risiko in der Score
  Engine.
- Nach jedem Sprint: `PROJECT_STATUS.md`, `CHANGELOG.md`, `ROADMAP.md`,
  `AI_CONTEXT.md`, `DECISIONS.md` und diese Datei aktualisieren.

## Nächster geplanter Schritt

**Sprint 8 – Risk Engine:** Ableitung von Risiko und Positionsgröße aus den
Scores. Details in `ROADMAP.md`.
