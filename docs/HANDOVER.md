# Handover (Übergabe)

_Diese Datei wird nach jedem Sprint automatisch aktualisiert._ Sie ermöglicht
es einer neuen Sitzung (Mensch oder KI), nahtlos weiterzuarbeiten – **ohne**
dass Wissen nur im Chat existiert.

## Stand der Übergabe

- **Datum:** 2026-07-08
- **Abgeschlossener Sprint:** Sprint 4 – Indicator Engine
- **Projektwurzel:** `AlphaAI/` (innerhalb des Repositorys `reiseplaner`)
- **Branch:** `claude/alphaai-project-bootstrap-c51pse`

## So startet die nächste Sitzung

1. In das Projektverzeichnis wechseln: `cd AlphaAI`.
2. Umgebung einrichten: `python3.12 -m venv .venv && source .venv/bin/activate`.
3. Installieren: `pip install -e ".[dev]"`.
4. Fundament prüfen: `python -m scripts.check_setup`.
5. Tests ausführen: `pytest` (aktuell 148 Tests).

## Qualitätsprüfung Sprint 4 (Ergebnis)

Vor dem Commit automatisch geprüft:

| Prüfung | Ergebnis |
|---|---|
| Import-Zyklen | **0** (44 Module per AST-Graph analysiert) |
| Indikator-Unabhängigkeit (kein Indikator hängt von anderem ab) | **0 Verstöße** |
| indicators.* importiert nicht aus engines.* | **eingehalten** |
| SOLID-Heuristik (genau eine Indikatorklasse, compute+min_candles) | **0 Verstöße** |
| Testabdeckung neuer Module (engines + indicators) | **92 %** (alle Indikatoren 100 %) |
| Ruff / Black | **konform** |
| pytest | **148 bestanden** |

Die Prüf-Heuristik: kein Modul in `indicators/` (außer `base.py`) importiert ein
anderes Indikatormodul oder aus `engines`; der Importgraph über alle Pakete ist
zyklenfrei.

## Indicator Engine – Kurzüberblick für die Weiterarbeit

- Einstieg: `IndicatorEngine.from_config()` erzeugt eine Engine mit Regeln aus
  `knowledge/indicator_rules.toml` und allen Standard-Indikatoren.
- Berechnung: `engine.calculate(ohlcv_df, symbol, timeframe)` oder
  `engine.calculate_symbol(market_result, symbol)` → `IndicatorResult`.
- Ergebnisfelder: `result.ema20/ema50/ema200`, `rsi14`, `atr14`, `vwap`,
  `macd/macd_signal/macd_histogram`, `relative_volume`, `adx`,
  `bollinger_bands`, `stochastic`, `obv`, `volume_profile` (+ `poc`). Volle
  Serien über `result.outputs[name].series`.
- **Neuen Indikator hinzufügen** (einziger erlaubter Weg):
  1. Datei in `indicators/` anlegen, `BaseIndicator` implementieren
     (`compute` + `min_candles`), nur OHLCV lesen, keine anderen Indikatoren.
  2. In `engines/indicator_registry.py::build_default_registry` registrieren.
  3. Parameter in `knowledge/indicator_rules.toml` ergänzen.
  4. Eigene Testdatei `tests/test_indicator_<name>.py` anlegen.
- **Multi-Timeframe** ist vorbereitet (Timeframe-Label in den Metadaten), aber
  noch nicht implementiert – ein späterer Aggregator ruft die Engine je
  Zeitebene auf.

## Wichtige Konventionen (unbedingt einhalten)

- **Keine hartcodierten Werte** – Parameter in `knowledge/*.toml`, Einstellungen
  in `config/*.toml`.
- **Type Hints und Docstrings** für jede öffentliche Funktion/Klasse.
- **Black- und Ruff-konform** (Zeilenlänge 100).
- **Abhängigkeiten zeigen nur nach unten**; kein Indikator hängt von einem
  anderen ab.
- **Kein Auto-Trading**, keine Scores/Signale in der Indicator Engine.
- Nach jedem Sprint: `PROJECT_STATUS.md`, `CHANGELOG.md`, `ROADMAP.md`,
  `AI_CONTEXT.md`, `DECISIONS.md` und diese Datei aktualisieren.

## Nächster geplanter Schritt

**Sprint 5 – Muster & Strategien:** Erkennung von Kursmustern in `patterns/`
und Setup-Bewertung in `strategies/`, jeweils regelbasiert über TOML. Details in
`ROADMAP.md`.
