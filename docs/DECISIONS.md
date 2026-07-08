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

### ADR-006 – Kanonisches OHLCV-Schema im MarketResult

- **Datum:** 2026-07-08
- **Kontext:** Verschiedene Provider liefern Kursdaten in unterschiedlichen
  Formaten (Spaltennamen, MultiIndex).
- **Entscheidung:** Jeder Provider normalisiert auf ein festes Schema
  (`open, high, low, close, adj_close, volume`, DatetimeIndex).
- **Begründung:** Nachgelagerte Schichten (Engines, Scanner) bleiben
  provider-unabhängig und einfach.
- **Konsequenzen:** Normalisierung ist Aufgabe des Providers; das Schema ist in
  `data/market_result.py` zentral definiert.

### ADR-007 – Dependency Injection für Netzwerk und Zeit

- **Datum:** 2026-07-08
- **Kontext:** Marktdaten (Netzwerk) und Cache-Ablauf (Zeit) sind schwer
  testbar, wenn sie fest verdrahtet sind.
- **Entscheidung:** Download-Funktion des Providers und Uhr des Caches sind
  injizierbar; Standardwerte greifen im Normalbetrieb.
- **Begründung:** Die gesamte Data Layer ist ohne echtes Netzwerk und ohne
  echtes Warten testbar (68 schnelle Tests).
- **Konsequenzen:** yfinance wird nur in der Standard-Download-Funktion und
  verzögert importiert.

### ADR-008 – Weitere Provider vorbereiten statt leer implementieren

- **Datum:** 2026-07-08
- **Kontext:** Finnhub, Polygon, AlphaVantage und IEX sollen vorbereitet, aber
  nicht implementiert werden.
- **Entscheidung:** Diese Provider sind in der Factory als „geplant" registriert
  und lösen beim Abruf einen klaren `ProviderNotImplementedError` aus – statt
  leerer Stub-Klassen.
- **Begründung:** Vermeidet Dummy-Code und stillschweigend falsche Ergebnisse;
  die Erweiterbarkeit ist dennoch dokumentiert und sichtbar.
- **Konsequenzen:** Implementierung erfordert später nur eine neue
  Provider-Klasse plus Registrierung.

### ADR-009 – Universen datengetrieben, mit Ehrlichkeits-Flag

- **Datum:** 2026-07-08
- **Kontext:** Vollständige Indexzusammensetzungen (v. a. S&P 500,
  Russell 2000) sind umfangreich und ändern sich; falsche „vollständige" Listen
  wären irreführend.
- **Entscheidung:** Universen stehen in `config/universe.toml`; jedes trägt ein
  Feld `complete`. Nur nachweislich vollständige Listen (DAX) sind als
  vollständig markiert, alle anderen als kuratierte Startliste.
- **Begründung:** Keine Hardcodes im Code, Anpassbarkeit ohne Programmierung und
  ehrliche Kennzeichnung der Datenqualität.
- **Konsequenzen:** Die Vervollständigung großer Universen erfolgt in einem
  späteren Sprint über eine Konstituenten-Quelle.

### ADR-005 – Logging zentral, idempotent, Konsole + Datei

- **Datum:** 2026-07-08
- **Kontext:** Nachvollziehbarkeit ist zentral; Mehrfach-Initialisierung (Tests,
  Streamlit-Reload) darf keine doppelten Ausgaben erzeugen.
- **Entscheidung:** `core/logging_config.py` richtet Logging einmalig ein und
  schreibt gleichzeitig auf Konsole und in eine rotierende Datei.
- **Begründung:** Einheitliche, dauerhafte und wiederholbar sichere Protokolle.
- **Konsequenzen:** Module holen sich Logger über `get_logger(__name__)`.
