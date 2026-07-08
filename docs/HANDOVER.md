# Handover (Übergabe)

_Diese Datei wird nach jedem Sprint automatisch aktualisiert._ Sie ermöglicht
es einer neuen Sitzung (Mensch oder KI), nahtlos weiterzuarbeiten – **ohne**
dass Wissen nur im Chat existiert.

## Stand der Übergabe

- **Datum:** 2026-07-08
- **Abgeschlossener Sprint:** Sprint 6 – Strategy Engine
- **Projektwurzel:** `AlphaAI/` (innerhalb des Repositorys `reiseplaner`)
- **Branch:** `claude/alphaai-project-bootstrap-c51pse`

## So startet die nächste Sitzung

1. In das Projektverzeichnis wechseln: `cd AlphaAI`.
2. Umgebung einrichten: `python3.12 -m venv .venv && source .venv/bin/activate`.
3. Installieren: `pip install -e ".[dev]"`.
4. Fundament prüfen: `python -m scripts.check_setup`.
5. Tests ausführen: `pytest` (aktuell 247 Tests).

## Qualitätsprüfung Sprint 6 (Ergebnis)

Vor dem Commit automatisch geprüft:

| Prüfung | Ergebnis |
|---|---|
| Import-Zyklen | **0** (72 Module per AST-Graph analysiert) |
| Strategie-Unabhängigkeit (keine Strategie hängt von anderer ab) | **0 Verstöße** |
| strategies.* importiert nicht aus engines.* | **eingehalten** |
| SOLID-Heuristik (genau eine Strategieklasse, evaluate) | **0 Verstöße** |
| Testabdeckung Strategy-Module (engines/strategy_*, strategies) | **96 %** |
| Ruff / Black | **konform** |
| pytest | **247 bestanden** |

## Strategy Engine – Kurzüberblick für die Weiterarbeit

- Einstieg: `StrategyEngine.from_config()` erzeugt eine Engine mit Regeln aus
  `knowledge/strategy_rules.toml` und allen Standard-Strategien.
- Auswertung: `engine.evaluate(indicator_result, pattern_report, data=ohlcv,
  symbol, timeframe)` → `StrategyReport` mit `StrategyResult`-Hypothesen.
- Ergebnis: `report.results`, Filter über `report.by_name(...)` /
  `report.by_direction(...)` / `report.bullish` / `report.bearish`.
- Jede Strategie deklariert `pattern_requirements` und
  `indicator_requirements`; die Engine überspringt Strategien mit fehlenden
  Anforderungen und vermerkt dies als Warnung.
- **Neue Strategie hinzufügen** (einziger erlaubter Weg):
  1. Datei in `strategies/` anlegen, `BaseStrategy` implementieren
     (`evaluate`), Anforderungen deklarieren, keine andere Strategie nutzen.
  2. In `engines/strategy_registry.py::build_default_registry` registrieren.
  3. Parameter in `knowledge/strategy_rules.toml` ergänzen.
  4. Eigene Testdatei `tests/test_strategy_<name>.py` anlegen.

## Wichtige Konventionen (unbedingt einhalten)

- **Keine hartcodierten Werte** – Parameter in `knowledge/*.toml`, Einstellungen
  in `config/*.toml`. Strength/Confidence sind beschreibende Kennzahlen der
  Hypothese, kein Gesamtscore.
- **Type Hints und Docstrings** für jede öffentliche Funktion/Klasse.
- **Black- und Ruff-konform** (Zeilenlänge 100).
- **Abhängigkeiten zeigen nur nach unten**; keine Strategie/kein Muster/kein
  Indikator hängt von einem anderen ab.
- **Kein Auto-Trading**, keine Kauf-/Verkaufsentscheidung, kein Gesamtscore in
  der Strategy Engine.
- Nach jedem Sprint: `PROJECT_STATUS.md`, `CHANGELOG.md`, `ROADMAP.md`,
  `AI_CONTEXT.md`, `DECISIONS.md` und diese Datei aktualisieren.

## Nächster geplanter Schritt

**Sprint 7 – Score Engine:** Aggregation der Strategie-Hypothesen zu einem
Gesamtscore je Symbol. Details in `ROADMAP.md`.
