# Entscheidungen (Architecture Decision Records)

_Wird laufend gepflegt._ Jede wesentliche Entscheidung wird hier kurz,
verständlich und begründet festgehalten. So bleibt nachvollziehbar, **warum**
das Projekt so aufgebaut ist, wie es ist.

## Format

```
### ADR-<Nr> – <Titel>
- Datum:
- Kontext: Welches Problem/Frage lag vor?
- Entscheidung: Was wurde festgelegt?
- Begründung: Warum?
- Konsequenzen: Was folgt daraus?
```

---

### ADR-001 – Projekt additiv im Unterordner `AlphaAI/`

- **Datum:** 2026-07-08
- **Kontext:** Das Repository enthielt bereits ein anderes Projekt
  (Reiseplaner, Next.js). Alpha AI ist ein eigenständiges Python-Projekt.
- **Entscheidung:** Alpha AI wird im Unterverzeichnis `AlphaAI/` angelegt; die
  bestehenden Dateien bleiben unangetastet.
- **Begründung:** Kein Verlust bestehender Arbeit; klare Trennung der beiden
  Projekte; die angeforderte Struktur mit `AlphaAI/` als Wurzel wird exakt
  abgebildet.
- **Konsequenzen:** Alle Alpha-AI-Pfade sind relativ zu `AlphaAI/`.

### ADR-002 – Konfiguration mit Standardbibliothek statt Zusatzpaket

- **Datum:** 2026-07-08
- **Kontext:** Einstellbare Parameter müssen geladen und validiert werden.
- **Entscheidung:** `config/settings.toml` wird mit `tomllib` (Standard in
  Python 3.12) gelesen und in `dataclasses` überführt.
- **Begründung:** Weniger Abhängigkeiten, leicht verständlich, ausreichend für
  den Umfang. Eine Validierungsbibliothek (z. B. Pydantic) wäre für das
  Fundament überdimensioniert.
- **Konsequenzen:** Validierung erfolgt explizit in `core/config.py`. Bei
  wachsender Komplexität kann später auf Pydantic umgestellt werden.

### ADR-003 – Unveränderliche Konfigurationsobjekte

- **Datum:** 2026-07-08
- **Kontext:** Konfiguration wird an viele Module weitergereicht.
- **Entscheidung:** Konfigurations-Datenklassen sind `frozen` (unveränderlich).
- **Begründung:** Verhindert versehentliche Änderungen zur Laufzeit und macht
  das Verhalten vorhersehbar; ideal für Dependency Injection.
- **Konsequenzen:** Änderungen erfordern das Neuladen der Konfiguration.

### ADR-004 – Parameter datengetrieben in `knowledge/*.toml`

- **Datum:** 2026-07-08
- **Kontext:** Indikatoren, Muster und Strategien sollen anpassbar sein, ohne
  Code zu ändern.
- **Entscheidung:** Deren Parameter leben in TOML-Dateien unter `knowledge/`.
- **Begründung:** Erfüllt die Vorgabe „keine Hardcodes" und ermöglicht
  Anpassungen ohne Programmierkenntnisse.
- **Konsequenzen:** Der spätere Code liest diese Dateien; das Format ist in
  Sprint 1 bereits festgelegt.

### ADR-005 – Logging zentral, idempotent, Konsole + Datei

- **Datum:** 2026-07-08
- **Kontext:** Nachvollziehbarkeit ist zentral; Mehrfach-Initialisierung (Tests,
  Streamlit-Reload) darf keine doppelten Ausgaben erzeugen.
- **Entscheidung:** `core/logging_config.py` richtet Logging einmalig ein und
  schreibt gleichzeitig auf Konsole und in eine rotierende Datei.
- **Begründung:** Einheitliche, dauerhafte und wiederholbar sichere Protokolle.
- **Konsequenzen:** Module holen sich Logger über `get_logger(__name__)`.
