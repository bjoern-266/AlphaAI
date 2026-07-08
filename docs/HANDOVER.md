# Handover (Übergabe)

_Diese Datei wird nach jedem Sprint automatisch aktualisiert._ Sie ermöglicht
es einer neuen Sitzung (Mensch oder KI), nahtlos weiterzuarbeiten – **ohne**
dass Wissen nur im Chat existiert.

## Stand der Übergabe

- **Datum:** 2026-07-08
- **Abgeschlossener Sprint:** Sprint 1 – Fundament
- **Projektwurzel:** `AlphaAI/` (innerhalb des Repositorys `reiseplaner`)
- **Branch:** `claude/alphaai-project-bootstrap-c51pse`

## So startet die nächste Sitzung

1. In das Projektverzeichnis wechseln: `cd AlphaAI`.
2. Umgebung einrichten: `python3.12 -m venv .venv && source .venv/bin/activate`.
3. Installieren: `pip install -e ".[dev]"`.
4. Fundament prüfen: `python -m scripts.check_setup`.
5. Tests ausführen: `pytest`.

## Was existiert bereits

- Vollständige Projektstruktur und Dokumentation (siehe `PROJECT_STATUS.md`).
- Funktionierendes Konfigurations- und Logging-System in `core/`.
- Wissensbasis in `knowledge/` mit definiertem Regel-/Parameterformat.

## Wichtige Konventionen (unbedingt einhalten)

- **Keine hartcodierten Werte** – alles Einstellbare gehört in
  `config/settings.toml` bzw. `knowledge/*.toml`.
- **Type Hints und Docstrings** für jede öffentliche Funktion/Klasse.
- **Black- und Ruff-konform** (Konfiguration in `pyproject.toml`,
  Zeilenlänge 100).
- **Abhängigkeiten zeigen nur nach unten** (siehe `ARCHITECTURE.md`).
- **Kein Auto-Trading** – Alpha AI erzeugt nur Empfehlungen.
- Nach jedem Sprint: `PROJECT_STATUS.md`, `CHANGELOG.md`, `ROADMAP.md`,
  `AI_CONTEXT.md`, `DECISIONS.md` und diese Datei aktualisieren.

## Nächster geplanter Schritt

**Sprint 2 – Datenquellen:** Provider-Schnittstelle und Marktdatenzugriff
(yfinance) inkl. Datenmodelle und Tests. Details in `ROADMAP.md`.
