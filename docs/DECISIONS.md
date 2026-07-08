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

### ADR-010 – Indikatoren direkt mit pandas/numpy statt pandas-ta

- **Datum:** 2026-07-08
- **Kontext:** Der Tech-Stack nennt `pandas-ta`. In der Zielumgebung liegen
  jedoch pandas 3.x und numpy 2.x vor; `pandas-ta` ist damit nicht kompatibel
  (nutzt entfernte numpy-Symbole).
- **Entscheidung:** Alle Indikatoren werden direkt mit pandas/numpy berechnet.
- **Begründung:** Robustheit, keine defekte Abhängigkeit, volle Kontrolle über
  die Formeln und die Unabhängigkeit der Indikatoren.
- **Konsequenzen:** `pandas-ta` bleibt optional; die Indikator-Mathematik ist im
  Projekt sichtbar und getestet.

### ADR-011 – Indikator-Unabhängigkeit über gemeinsame Basis

- **Datum:** 2026-07-08
- **Kontext:** Kein Indikator darf von einem anderen abhängen; dennoch nutzen
  ATR und ADX dieselbe True-Range-Berechnung.
- **Entscheidung:** Gemeinsame Hilfsmittel (True Range, sichere Division,
  Parameterprüfung) liegen in `indicators/base.py`; Indikatoren importieren nur
  von dort, nie voneinander.
- **Begründung:** Vermeidet Duplikate ohne die Unabhängigkeitsregel zu
  verletzen; ein automatischer Check erzwingt die Regel.
- **Konsequenzen:** `base.py` ist bewusst kein Indikator, sondern Infrastruktur.

### ADR-012 – Registry als einzige Erweiterungsstelle

- **Datum:** 2026-07-08
- **Kontext:** Neue Indikatoren sollen ohne Eingriff in die Engine ergänzbar
  sein.
- **Entscheidung:** Die Engine kennt nur die `IndicatorRegistry`. Neue
  Indikatoren werden dort registriert; Parameter kommen aus TOML.
- **Begründung:** Open/Closed-Prinzip – die Engine bleibt geschlossen für
  Änderungen, offen für Erweiterungen.
- **Konsequenzen:** Ein Indikator ohne Registrierung wird nicht berechnet.

### ADR-013 – Muster-Ergebnistypen in patterns/base.py

- **Datum:** 2026-07-08
- **Kontext:** Die Registry (in `engines`) importiert alle Muster; Muster
  müssen ihren Ergebnistyp kennen. Läge `PatternResult` in `engines`, entstünde
  ein Import-Zyklus `patterns → engines → patterns`.
- **Entscheidung:** `PatternResult`, `PatternType` und `PatternDirection` liegen
  in `patterns/base.py`; `engines/pattern_result.py` re-exportiert sie und
  definiert zusätzlich das Aggregat `PatternReport`.
- **Begründung:** Zyklenfreiheit bei gleichzeitig klarer Zuordnung (analog zu
  `IndicatorOutput` in `indicators/base.py`).
- **Konsequenzen:** Ein automatischer Check bestätigt: keine Zyklen, `patterns`
  importiert nicht aus `engines`.

### ADR-014 – Gemeinsame Struktur-/Swing-Helfer statt Muster-Abhängigkeiten

- **Datum:** 2026-07-08
- **Kontext:** BOS, CHoCH, Market Structure und Trend Structure benötigen
  dieselbe Swing-/Struktur-Break-Logik; Equal Highs/Lows und Liquidity Sweep
  benötigen Swings.
- **Entscheidung:** Diese Hilfsmittel liegen in `patterns/base.py`; kein Muster
  importiert ein anderes Muster.
- **Begründung:** Erfüllt die Regel „kein Muster hängt von einem anderen ab"
  ohne Code-Duplikate; die Klassifikation BOS vs. CHoCH ist an einer Stelle
  definiert und getestet.
- **Konsequenzen:** BOS/CHoCH filtern lediglich die Ereignisse des gemeinsamen
  Helpers nach Typ.

### ADR-015 – Beschreibende Strength/Confidence, keine Signale

- **Datum:** 2026-07-08
- **Kontext:** `PatternResult` trägt `strength` (0-100) und `confidence` (0-1).
  Diese könnten als Handelssignal missverstanden werden.
- **Entscheidung:** Beide sind rein **beschreibende** Kennzahlen der Erkennung
  (z. B. Gap-Größe, Mitigations-Zustand), keine Kauf-/Verkaufsbewertung. Die
  Skalierungskonstanten sind dokumentierte Algorithmus-Bestandteile; tunbare
  Schwellen (Lookback, Toleranz, Mindest-Gap) stehen in TOML.
- **Begründung:** Klare Trennung zwischen Beschreibung (Pattern Engine) und
  Bewertung (spätere Strategy-/Score-Engine).
- **Konsequenzen:** Die Pattern Engine bleibt frei von Handelslogik.

### ADR-016 – Strategie-Ergebnistypen in strategies/base.py

- **Datum:** 2026-07-08
- **Kontext:** Wie bei den Mustern importiert die Registry (in `engines`) alle
  Strategien; läge `StrategyResult` in `engines`, entstünde ein Import-Zyklus.
- **Entscheidung:** `StrategyResult`, `StrategyContext`, `StrategyEvaluation`
  und `StrategyDirection` liegen in `strategies/base.py`;
  `engines/strategy_result.py` re-exportiert sie und definiert das Aggregat
  `StrategyReport`. Verweise auf `IndicatorResult`/`PatternReport` erfolgen nur
  unter `TYPE_CHECKING`.
- **Begründung:** Zyklenfreiheit; ein automatischer Check bestätigt dies.
- **Konsequenzen:** Strategien nutzen die Engine-Ergebnisse per Duck-Typing zur
  Laufzeit (keine harten Engine-Importe).

### ADR-017 – Strategien liefern Hypothesen, keine Scores/Entscheidungen

- **Datum:** 2026-07-08
- **Kontext:** `StrategyResult` trägt `strength` und `confidence`; diese dürfen
  nicht als Kauf-/Verkaufsentscheidung oder Gesamtscore missverstanden werden.
- **Entscheidung:** Jede Strategie erzeugt ausschließlich eine **Hypothese**
  (Richtung + Begründungen, z. B. „Bullische Trendfortsetzung"). `strength` und
  `confidence` sind beschreibende Kennzahlen der Hypothese (aus Muster-Stärken
  bzw. konfigurierter Basis-Confidence), kein aggregierter Score. Die
  Aggregation zu einem Gesamtscore ist Aufgabe der späteren Score Engine.
- **Begründung:** Klare Trennung Hypothese (Sprint 6) ↔ Bewertung (Score
  Engine, später) ↔ Empfehlung (Recommendation Engine, später).
- **Konsequenzen:** Die Strategy Engine bleibt frei von Handelslogik.

### ADR-018 – Anforderungen als deklarative Strategie-Attribute

- **Datum:** 2026-07-08
- **Kontext:** Strategien benötigen bestimmte Indikatoren/Muster; fehlen diese,
  darf keine Hypothese erzwungen werden.
- **Entscheidung:** Jede Strategie deklariert `indicator_requirements` und
  `pattern_requirements`. Die Engine prüft sie vor der Auswertung und
  überspringt Strategien mit fehlenden Anforderungen mit einer Warnung.
- **Begründung:** Erfüllt die Validierungsvorgaben (fehlende Indikatoren/Muster)
  zentral und testbar, ohne jede Strategie mit Prüf-Code zu belasten.
- **Konsequenzen:** Strategien konzentrieren sich auf ihre Fachlogik.

### ADR-005 – Logging zentral, idempotent, Konsole + Datei

- **Datum:** 2026-07-08
- **Kontext:** Nachvollziehbarkeit ist zentral; Mehrfach-Initialisierung (Tests,
  Streamlit-Reload) darf keine doppelten Ausgaben erzeugen.
- **Entscheidung:** `core/logging_config.py` richtet Logging einmalig ein und
  schreibt gleichzeitig auf Konsole und in eine rotierende Datei.
- **Begründung:** Einheitliche, dauerhafte und wiederholbar sichere Protokolle.
- **Konsequenzen:** Module holen sich Logger über `get_logger(__name__)`.
