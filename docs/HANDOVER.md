# Handover (Übergabe)

_Diese Datei wird nach jedem Sprint automatisch aktualisiert._ Sie ermöglicht
es einer neuen Sitzung (Mensch oder KI), nahtlos weiterzuarbeiten – **ohne**
dass Wissen nur im Chat existiert.

## Stand der Übergabe

- **Datum:** 2026-07-08
- **Abgeschlossener Sprint:** Sprint 7 – Score Engine
- **Projektwurzel:** `AlphaAI/` (innerhalb des Repositorys `reiseplaner`)
- **Branch:** `claude/alphaai-project-bootstrap-c51pse`

## So startet die nächste Sitzung

1. In das Projektverzeichnis wechseln: `cd AlphaAI`.
2. Umgebung einrichten: `python3.12 -m venv .venv && source .venv/bin/activate`.
3. Installieren: `pip install -e ".[dev]"`.
4. Fundament prüfen: `python -m scripts.check_setup`.
5. Tests ausführen: `pytest` (aktuell 307 Tests).

## Qualitätsprüfung Sprint 7 (Ergebnis)

Vor dem Commit automatisch geprüft:

| Prüfung | Ergebnis |
|---|---|
| Import-Zyklen | **0** (83 Module per AST-Graph analysiert) |
| Score-Modell-Unabhängigkeit (kein Modell hängt von anderem ab) | **0 Verstöße** |
| scores.* importiert nicht aus engines.* | **eingehalten** |
| SOLID-Heuristik (genau eine Modellklasse, compute) | **0 Verstöße** |
| Testabdeckung Score-Module (engines/score_*, scores) | **96 %** |
| Ruff / Black | **konform** |
| pytest | **307 bestanden** |

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
