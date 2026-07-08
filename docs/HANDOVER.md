# Handover (Übergabe)

_Diese Datei wird nach jedem Sprint automatisch aktualisiert._ Sie ermöglicht
es einer neuen Sitzung (Mensch oder KI), nahtlos weiterzuarbeiten – **ohne**
dass Wissen nur im Chat existiert.

## Stand der Übergabe

- **Datum:** 2026-07-08
- **Abgeschlossener Sprint:** Sprint 3 – Scanner Core
- **Projektwurzel:** `AlphaAI/` (innerhalb des Repositorys `reiseplaner`)
- **Branch:** `claude/alphaai-project-bootstrap-c51pse`

## So startet die nächste Sitzung

1. In das Projektverzeichnis wechseln: `cd AlphaAI`.
2. Umgebung einrichten: `python3.12 -m venv .venv && source .venv/bin/activate`.
3. Installieren: `pip install -e ".[dev]"`.
4. Fundament prüfen: `python -m scripts.check_setup`.
5. Tests ausführen: `pytest` (aktuell 95 Tests).

## Schichten (jede kennt nur die darunterliegende)

```
ScannerManager → ScannerEngine → ScanPipeline → MarketDataEngine
                                       │                 │
                                 ScanStatistics    Repository → Provider
                                                        │
                                                  Cache + Validator
```

## Scanner Core – Kurzüberblick für die Weiterarbeit

- Einstieg ist die `ScannerEngine.scan(request)` bzw. für mehrere Läufe der
  `ScannerManager.scan_all(...)`.
- Der Scanner Core macht **nur Orchestrierung** – keine Analyse. Die
  Ergebnisfelder `indicators`, `patterns`, `score`, `risk`, `recommendation` im
  `ScanResult` sind vorbereitet und werden ab Sprint 4 befüllt.
- Verdrahtung (Composition Root) für einen lauffähigen Scanner:
  1. `repository = build_repository(settings)` (Data Layer).
  2. `engine = MarketDataEngine(repository, settings)`.
  3. `pipeline = ScanPipeline(engine)`.
  4. `scanner = ScannerEngine(pipeline)`.
  5. optional `manager = ScannerManager(scanner, settings)`.
- Anfragen bevorzugt über `build_scan_request(settings, ...)` erzeugen – füllt
  `requested_features`/`max_workers` aus der Konfiguration.
- `max_workers` ist vorbereitet, aber ungenutzt (noch keine Parallelisierung).

## Wichtige Konventionen (unbedingt einhalten)

- **Keine hartcodierten Werte** – alles Einstellbare gehört in
  `config/settings.toml`, `config/universe.toml` bzw. `knowledge/*.toml`.
- **Type Hints und Docstrings** für jede öffentliche Funktion/Klasse.
- **Black- und Ruff-konform** (Konfiguration in `pyproject.toml`,
  Zeilenlänge 100).
- **Abhängigkeiten zeigen nur nach unten** (siehe `ARCHITECTURE.md`).
- **Kein Auto-Trading** – Alpha AI erzeugt nur Empfehlungen.
- Nach jedem Sprint: `PROJECT_STATUS.md`, `CHANGELOG.md`, `ROADMAP.md`,
  `AI_CONTEXT.md`, `DECISIONS.md` und diese Datei aktualisieren.

## Nächster geplanter Schritt

**Sprint 4 – Analyse-Engines / Indikatoren:** Berechnung technischer Indikatoren
in `engines/` (parametrisiert über `knowledge/indicator_rules.toml`) und
Befüllung von `ScanResult.indicators`. Details in `ROADMAP.md`.
