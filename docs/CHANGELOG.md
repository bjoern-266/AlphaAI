# Changelog

_Wird nach jedem Sprint automatisch aktualisiert._ Das Format orientiert sich
an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/) und
[Semantic Versioning](https://semver.org/lang/de/).

## [0.1.0] – 2026-07-08 – Sprint 1: Fundament

### Hinzugefügt

- Modulare Projektstruktur unter `AlphaAI/` (core, config, knowledge, data,
  providers, scanner, engines, patterns, strategies, dashboard, database,
  models, tests, docs, logs, output, scripts).
- Kernschicht `core/`:
  - `paths.py` – zentrale Projektpfade, keine hartcodierten Pfade.
  - `exceptions.py` – projektweite Fehlerklassen (`AlphaAIError`, `ConfigError`).
  - `config.py` – Laden/Validieren von `settings.toml` in typisierte,
    unveränderliche Datenklassen (Fail-Fast).
  - `logging_config.py` – einheitliches, idempotentes Logging (Konsole + Datei).
- Konfigurationsdatei `config/settings.toml` (Depot, Broker, Fractional
  Shares, Risiko, Handelszeiten, Märkte).
- Wissensbasis `knowledge/` (Markdown-Regeln + TOML-Parameterdateien).
- Prüfskript `scripts/check_setup.py`.
- Dokumentation `docs/` (Architektur, Status, Roadmap, Changelog, Handover,
  AI-Kontext, Entscheidungen).
- Basistests (`tests/`) für Konfiguration, Logging und Projektstruktur.
- Werkzeugkonfiguration in `pyproject.toml` (Black, Ruff, pytest).
- `.gitignore` für Python- und Laufzeit-Artefakte.

### Hinweis

Bewusst noch nicht enthalten: Scanner, Datenquellen, Indikatoren, Muster,
Strategien und Handelslogik. Diese folgen ab Sprint 2.
