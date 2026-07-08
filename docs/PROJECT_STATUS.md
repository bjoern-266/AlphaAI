# Projektstatus

_Wird nach jedem Sprint automatisch aktualisiert._

- **Datum:** 2026-07-08
- **Aktueller Sprint:** Sprint 1 – Fundament
- **Status:** ✅ Abgeschlossen

## Was ist vorhanden

- Vollständige, modulare Projektstruktur (`AlphaAI/`).
- Konfigurations-System (`config/settings.toml` + `core/config.py`) mit
  Validierung und typisierten, unveränderlichen Datenklassen.
- Zentrale Pfadverwaltung (`core/paths.py`) – keine hartcodierten Pfade.
- Einheitliches Logging (`core/logging_config.py`, Konsole + rotierende Datei).
- Projektweite Fehlerklassen (`core/exceptions.py`).
- Prüfskript `scripts/check_setup.py` (verifiziert das Fundament).
- Wissensbasis in `knowledge/` (Regeln als Markdown, Parameter als TOML).
- Vollständige Dokumentation in `docs/`.
- Basistests mit pytest (Konfiguration, Logging, Struktur).
- Werkzeugkonfiguration in `pyproject.toml` (Black, Ruff, pytest).

## Was ist bewusst NICHT vorhanden

- Kein Scanner.
- Keine Datenquellen / APIs.
- Keine Indikatoren / Engines.
- Keine Muster- oder Strategielogik.
- Kein Dashboard mit Inhalten.

Diese Teile folgen ab Sprint 2 (siehe `ROADMAP.md`).

## Nächster Schritt

Warten auf Freigabe für **Sprint 2 – Datenquellen** (Provider-Schnittstelle
und Marktdatenzugriff).
