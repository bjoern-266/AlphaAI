# Alpha AI

**Alpha AI** ist eine modulare Analyseplattform für das Daytrading.

> **Wichtig:** Alpha AI handelt **nicht** automatisch. Die Plattform
> analysiert Märkte, erkennt statistisch hochwertige Setups und erzeugt
> **nachvollziehbare Empfehlungen**. Die Handelsentscheidung trifft immer
> der Mensch.

## Projektziel

- Märkte systematisch analysieren.
- Statistisch hochwertige Daytrading-Setups erkennen.
- Nachvollziehbare, begründete Empfehlungen erzeugen.
- Langfristig lernfähig werden (Auswertung eigener Empfehlungen).

## Installation

Voraussetzung: **Python 3.12**.

```bash
# In das Projektverzeichnis wechseln
cd AlphaAI

# Virtuelle Umgebung anlegen und aktivieren
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Projekt inkl. Entwicklungswerkzeuge installieren
pip install -e ".[dev]"

# Fundament prüfen (lädt Konfiguration, richtet Logging ein)
python -m scripts.check_setup

# Tests ausführen
pytest
```

## Ordnerstruktur

```
AlphaAI/
├── core/         # Technische Grundbausteine (Config, Logging, Pfade, Fehler)
├── config/       # settings.toml – alle einstellbaren Parameter
├── knowledge/    # Wissensbasis: Regeln (Markdown) und Parameter (TOML)
├── data/         # Datenschicht: Marktdaten-Modelle und -Zugriff
├── providers/    # Datenquellen (z. B. yfinance) hinter einer Schnittstelle
├── scanner/      # Orchestrierung der Analyse
├── engines/      # Berechnung technischer Kennzahlen/Indikatoren
├── patterns/     # Erkennung von Kursmustern
├── strategies/   # Bewertung von Setups
├── dashboard/    # Streamlit-Oberfläche (Charts via Plotly)
├── database/     # Persistenz (SQLite)
├── models/       # Domänenmodelle (schichtenübergreifend)
├── tests/        # pytest-Tests
├── docs/         # Projektdokumentation (Architektur, Status, Roadmap, …)
├── logs/         # Laufzeit-Logs (nicht versioniert)
├── output/       # Erzeugte Ausgaben (nicht versioniert)
└── scripts/      # Ausführbare Hilfsskripte
```

## Technologie

Python 3.12 · FastAPI · Streamlit · SQLite · Plotly · yfinance ·
pandas · numpy · pandas-ta · pytest · TOML

## Roadmap (Kurzfassung)

- **Sprint 1 – Fundament (aktuell):** Projektstruktur, Konfiguration,
  Logging, Tests, Dokumentation.
- **Sprint 2 – Datenquellen:** Provider-Schnittstelle und Marktdatenzugriff.
- **Sprint 3 – Analyse-Engines:** technische Indikatoren.
- **Sprint 4 – Muster & Strategien:** Setup-Erkennung und -Bewertung.
- **Sprint 5 – Dashboard:** Visualisierung und Empfehlungen.
- **Sprint 6 – Lernfähigkeit:** Auswertung und Journalisierung.

Die vollständige Roadmap steht in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Dokumentation

Alle wichtigen Informationen leben in `docs/` und werden nach **jedem Sprint**
aktualisiert – nichts existiert nur im Chat:

- [`ARCHITECTURE.md`](docs/ARCHITECTURE.md) – Aufbau und Schichten.
- [`PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) – aktueller Stand.
- [`ROADMAP.md`](docs/ROADMAP.md) – geplante Sprints.
- [`CHANGELOG.md`](docs/CHANGELOG.md) – Änderungshistorie.
- [`HANDOVER.md`](docs/HANDOVER.md) – Übergabe für die nächste Sitzung.
- [`AI_CONTEXT.md`](docs/AI_CONTEXT.md) – Kontext für KI-Modelle.
- [`DECISIONS.md`](docs/DECISIONS.md) – begründete Entscheidungen.
