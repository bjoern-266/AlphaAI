# Handover (Übergabe)

_Diese Datei wird nach jedem Sprint automatisch aktualisiert._ Sie ermöglicht
es einer neuen Sitzung (Mensch oder KI), nahtlos weiterzuarbeiten – **ohne**
dass Wissen nur im Chat existiert.

## Stand der Übergabe

- **Datum:** 2026-07-08
- **Abgeschlossener Sprint:** Sprint 5 – Pattern Engine
- **Projektwurzel:** `AlphaAI/` (innerhalb des Repositorys `reiseplaner`)
- **Branch:** `claude/alphaai-project-bootstrap-c51pse`

## So startet die nächste Sitzung

1. In das Projektverzeichnis wechseln: `cd AlphaAI`.
2. Umgebung einrichten: `python3.12 -m venv .venv && source .venv/bin/activate`.
3. Installieren: `pip install -e ".[dev]"`.
4. Fundament prüfen: `python -m scripts.check_setup`.
5. Tests ausführen: `pytest` (aktuell 197 Tests).

## Qualitätsprüfung Sprint 5 (Ergebnis)

Vor dem Commit automatisch geprüft:

| Prüfung | Ergebnis |
|---|---|
| Import-Zyklen | **0** (61 Module per AST-Graph analysiert) |
| Muster-Unabhängigkeit (kein Muster hängt von anderem ab) | **0 Verstöße** |
| patterns.* importiert nicht aus engines.* | **eingehalten** |
| SOLID-Heuristik (genau eine Musterklasse, detect+min_candles) | **0 Verstöße** |
| Testabdeckung Pattern-Module (engines/pattern_*, patterns) | **95 %** |
| Ruff / Black | **konform** |
| pytest | **197 bestanden** |

## Pattern Engine – Kurzüberblick für die Weiterarbeit

- Einstieg: `PatternEngine.from_config()` erzeugt eine Engine mit Regeln aus
  `knowledge/pattern_rules.toml` und allen Standard-Mustern.
- Erkennung: `engine.detect(ohlcv_df, symbol, timeframe)` oder
  `engine.detect_symbol(market_result, symbol)` → `PatternReport`.
- Ergebnis: `report.results` (Liste von `PatternResult`), Filter über
  `report.by_name(...)` / `report.by_direction(...)`.
- **Neues Muster hinzufügen** (einziger erlaubter Weg):
  1. Datei in `patterns/` anlegen, `BasePattern` implementieren
     (`detect` + `min_candles`), nur OHLCV lesen, keine anderen Muster.
  2. In `engines/pattern_registry.py::build_default_registry` registrieren.
  3. Parameter in `knowledge/pattern_rules.toml` ergänzen.
  4. Eigene Testdatei `tests/test_pattern_<name>.py` anlegen.
- Die drei Block-Muster sind vorbereitet (`implemented = False`) – bei der
  Umsetzung nur `implemented` entfernen und `detect` füllen.

## Wichtige Konventionen (unbedingt einhalten)

- **Keine hartcodierten Werte** – Parameter in `knowledge/*.toml`, Einstellungen
  in `config/*.toml`. Scoring-Skalen (strength/confidence) sind dokumentierte
  algorithmische Konstanten, keine Tuning-Parameter.
- **Type Hints und Docstrings** für jede öffentliche Funktion/Klasse.
- **Black- und Ruff-konform** (Zeilenlänge 100).
- **Abhängigkeiten zeigen nur nach unten**; kein Muster/Indikator hängt von
  einem anderen ab.
- **Kein Auto-Trading**, keine Scores/Signale in Indicator- oder Pattern-Engine.
- Nach jedem Sprint: `PROJECT_STATUS.md`, `CHANGELOG.md`, `ROADMAP.md`,
  `AI_CONTEXT.md`, `DECISIONS.md` und diese Datei aktualisieren.

## Nächster geplanter Schritt

**Sprint 6 – Strategien:** Setup-Bewertung in `strategies/` auf Basis der
Indikator- und Muster-Ergebnisse, regelbasiert über
`knowledge/strategy_rules.toml`. Details in `ROADMAP.md`.
