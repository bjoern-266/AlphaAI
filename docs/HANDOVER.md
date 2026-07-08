# Handover (Übergabe)

_Diese Datei wird nach jedem Sprint automatisch aktualisiert._ Sie ermöglicht
es einer neuen Sitzung (Mensch oder KI), nahtlos weiterzuarbeiten – **ohne**
dass Wissen nur im Chat existiert.

## Stand der Übergabe

- **Datum:** 2026-07-08
- **Abgeschlossener Sprint:** Sprint 2 – Data Layer
- **Projektwurzel:** `AlphaAI/` (innerhalb des Repositorys `reiseplaner`)
- **Branch:** `claude/alphaai-project-bootstrap-c51pse`

## So startet die nächste Sitzung

1. In das Projektverzeichnis wechseln: `cd AlphaAI`.
2. Umgebung einrichten: `python3.12 -m venv .venv && source .venv/bin/activate`.
3. Installieren: `pip install -e ".[dev]"`.
4. Fundament prüfen: `python -m scripts.check_setup`.
5. Tests ausführen: `pytest` (aktuell 68 Tests).

## Data Layer – Kurzüberblick für die Weiterarbeit

Die Schichten (jede kennt nur die darunterliegende):

```
MarketDataEngine  →  MarketRepository  →  Provider  →  externe Quelle
                              │
                        Cache + Validator
```

- Einstieg für nachgelagerte Schichten ist **immer** die `MarketDataEngine`
  (`data/market_data_engine.py`). Der spätere Scanner nutzt ausschließlich sie.
- Ergebnis ist ein `MarketResult` mit kanonischem OHLCV-Schema
  (Spalten `open, high, low, close, adj_close, volume`).
- Objekte werden über `repository_factory.build_repository(settings)` erzeugt
  (Composition Root). Provider, Cache-Uhr und Universums-Auflösung sind für
  Tests injizierbar.
- Neue Datenquelle hinzufügen: `BaseProvider` implementieren und in
  `providers/provider_factory.py` registrieren.
- Symbollisten werden nie im Code gepflegt, sondern in `config/universe.toml`.

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

**Sprint 3 – Analyse-Engines:** technische Indikatoren in `engines/` auf Basis
der Data Layer, parametrisiert über `knowledge/indicator_rules.toml`. Details
in `ROADMAP.md`.
