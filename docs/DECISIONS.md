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

### ADR-019 – Komponenten getrennt von Score-Modellen

- **Datum:** 2026-07-08
- **Kontext:** Mehrere Score-Modelle nutzen dieselben acht Komponenten (Trend,
  Momentum, …). Würden Modelle Komponenten voneinander beziehen, entstünden
  Abhängigkeiten zwischen Modellen.
- **Entscheidung:** Die Komponenten-Berechnung liegt zentral in
  `scores/base.py::compute_components`; die Engine berechnet sie einmal je
  Hypothese und übergibt sie über den `ScoreContext`. Modelle lesen nur
  Komponenten, nie ein anderes Modell.
- **Begründung:** Erfüllt die Score-Modell-Unabhängigkeit ohne Duplikate; ein
  automatischer Check bestätigt dies.
- **Konsequenzen:** Neue Komponenten werden an einer Stelle ergänzt und stehen
  allen Modellen zur Verfügung.

### ADR-020 – Engine bleibt bei neuen Score-Modellen unverändert

- **Datum:** 2026-07-08
- **Kontext:** Neue Score-Modelle sollen ohne Eingriff in die Engine ergänzbar
  sein; zugleich hat `ScoreResult` benannte Felder (total/confidence/…).
- **Entscheidung:** Die Engine führt **alle** registrierten und aktivierten
  Modelle generisch aus und legt deren Werte in `metadata['model_scores']` ab.
  Die benannten Felder werden aus wohlbekannten Modellnamen befüllt; unbekannte
  Modelle erscheinen zusätzlich in den Metadaten.
- **Begründung:** Open/Closed-Prinzip – Registry und TOML genügen, die Engine
  bleibt geschlossen.
- **Konsequenzen:** Der Sektionsname in `score_rules.toml` muss dem Modellnamen
  entsprechen.

### ADR-021 – Scores sind beschreibend, keine Entscheidung

- **Datum:** 2026-07-08
- **Kontext:** Ein Gesamtscore könnte als Kaufsignal missverstanden werden.
- **Entscheidung:** Die Score Engine berechnet ausschließlich objektive,
  vollständig erklärbare Scores (Komponenten-Aufschlüsselung). Sie erzeugt keine
  Kauf-/Verkaufsentscheidung, keine Positionsgröße und kein Risiko;
  `ScoreReport.top()` ist reine Sortierung/Anzeige.
- **Begründung:** Klare Trennung Bewertung (Sprint 7) ↔ Risiko (Sprint 8) ↔
  Empfehlung (später).
- **Konsequenzen:** Die Score Engine bleibt frei von Handelslogik.

### ADR-005 – Logging zentral, idempotent, Konsole + Datei

- **Datum:** 2026-07-08
- **Kontext:** Nachvollziehbarkeit ist zentral; Mehrfach-Initialisierung (Tests,
  Streamlit-Reload) darf keine doppelten Ausgaben erzeugen.
- **Entscheidung:** `core/logging_config.py` richtet Logging einmalig ein und
  schreibt gleichzeitig auf Konsole und in eine rotierende Datei.
- **Begründung:** Einheitliche, dauerhafte und wiederholbar sichere Protokolle.
- **Konsequenzen:** Module holen sich Logger über `get_logger(__name__)`.

---

### ADR-022 – Domänenmodelle in `models/` (Entities-Schicht) mit Re-Exports

- **Datum:** 2026-07-09 (Sprint 7.5)
- **Kontext:** Ergebnis-/Datentypen lagen verstreut (`data.market_result`,
  `engines/*_result.py`, `*/base.py`). Das erschwerte Clean Architecture und
  koppelte `strategies`/`scores` über `TYPE_CHECKING` an `engines`.
- **Entscheidung:** Alle reinen Datencontainer werden in `models/` gebündelt
  (`market`, `indicator`, `pattern`, `strategy`, `score`; `risk`/
  `recommendation` vorbereitet). Die bisherigen Pfade re-exportieren die Typen.
- **Begründung:** `models/` ist die blattnahe Entities-Schicht und importiert
  nichts aus höheren Schichten; Engines und `*/base.py` enthalten nur Logik.
  Re-Exports erhalten alle öffentlichen Importpfade (keine Teständerung nötig).
- **Konsequenzen:** Neue Datentypen entstehen in `models/`; die frühere
  `engines`-Kopplung von `strategies`/`scores` entfällt (TD-05 gelöst).

### ADR-023 – Unveränderliche (frozen) Ergebnisobjekte

- **Datum:** 2026-07-09 (Sprint 7.5)
- **Kontext:** Reports wurden von den Engines nach der Erstellung mutiert
  (`report.valid = …`, `report.calculation_time = …`).
- **Entscheidung:** Alle Modelle sind `frozen`. Die Engines sammeln
  Zwischenstände in lokalen Akkumulatoren und konstruieren das Ergebnis
  **einmalig am Ende**; die Rechenzeit wird über `dataclasses.replace()` gesetzt.
- **Begründung:** Unveränderliche Ergebnisse sind sicherer (kein versehentliches
  Verändern, cache-fest, threadfreundlicher) und machen die Datenflüsse klar.
- **Konsequenzen:** Kein Code verändert ein Ergebnisobjekt nach der Erstellung;
  Änderungen erzeugen bewusst eine Kopie via `replace()`.

### ADR-024 – Generische `Cache[T]` und `Registry[T]` in `core/`

- **Datum:** 2026-07-09 (Sprint 7.5)
- **Kontext:** Cache- und Registry-Logik existierte viermal nahezu identisch.
- **Entscheidung:** Eine generische `Cache[T]` (FIFO, Trefferzählung) und
  `Registry[T]` in `core/`; die vier Engine-Caches/-Registries erben nur noch.
- **Begründung:** Weniger Duplikat, eine Stelle für Verhalten/Fehler; das
  öffentliche Interface (`get`/`set`/`register`/`names`/…) bleibt unverändert.
- **Konsequenzen:** Ein künftiger Risk-Cache nutzt dieselbe Basis.

### ADR-025 – Einheitliche Exception-Hierarchie unter `AlphaAIError`

- **Datum:** 2026-07-09 (Sprint 7.5)
- **Kontext:** Fachliche Fehler wurden teils als blankes `ValueError`/`KeyError`
  ausgelöst; es fehlte eine gemeinsame Wurzel.
- **Entscheidung:** Alle fachlichen Fehler stammen aus `AlphaAIError`
  (`ParameterError`, `RegistryError`, `CacheError` …). Zur
  Rückwärtskompatibilität erben ausgewählte Klassen zusätzlich von
  `ValueError` bzw. `KeyError`.
- **Begründung:** Aufrufer können alle Alpha-AI-Fehler mit `except AlphaAIError`
  gezielt fangen; bestehende `except ValueError`-Erwartungen bleiben gültig.
- **Konsequenzen:** Kein blankes `ValueError`/`KeyError` mehr für Fachfehler.

### ADR-026 – PEP-695-Generics bewusst vermieden

- **Datum:** 2026-07-09 (Sprint 7.5)
- **Kontext:** `ruff` (UP046/UP047) empfiehlt die 3.12-Syntax `class C[T]`.
- **Entscheidung:** Es wird weiterhin `typing.Generic[T]`/`TypeVar` verwendet;
  UP046/UP047 sind in `ruff` ignoriert.
- **Begründung:** Die `class C[T]`-Syntax ist erst ab Python 3.12 lauffähig; die
  Ausführungs-/Testumgebung nutzt teils 3.11. `Generic[T]` läuft überall gleich.
- **Konsequenzen:** Wird die Mindestversion strikt auf 3.12 gehoben, kann die
  Entscheidung revidiert werden.

### ADR-027 – Risk Engine: Komponenten, Positionsgröße, Portfolio-Vorbereitung

- **Datum:** 2026-07-09 (Sprint 8)
- **Kontext:** Nach dem Score braucht jede Hypothese eine objektive, erklärbare
  Risikobewertung samt Positionsgrößen-Empfehlung – ohne Handelsentscheidung.
- **Entscheidung:**
  - Kette `ScoreReport → RiskEngine → RiskReport`; die Engine ist konsistent zu
    den anderen Engines gebaut (frozen `models/risk.py`, generische
    `Cache`/`Registry`, `AlphaAIError`-Hierarchie, Bau-am-Ende + `replace()`).
  - Das Gesamtrisiko (0..100) ist die gewichtete Summe **zehn** getrennter
    Komponenten (Gewichte aus `[overall]` in `risk_rules.toml`, Summe 100 %).
    Sieben Komponenten liefern registrierte Modelle (`risk/*.py`), drei sind
    Basis-Helfer in `risk/base.py` (ATR, Datenqualität, News – News neutral
    vorbereitet).
  - **Positionsgröße** ist eigenes Modell (`position_sizing`) ohne Beitrag zum
    Gesamtrisiko; die Engine liest seine Kennzahlen aus `details['sizing']`
    (analog zu `_FIELD_MODELS` der Score Engine). Konto-/Depotwerte kommen
    ausschließlich aus `settings.toml`, Ausführungskosten aus `risk_rules.toml`.
  - **Portfolio-Vorbereitung:** `RiskContext` führt `open_positions`; Portfolio-
    und Korrelationsrisiko sind bereits verdrahtet (heute 0 ohne Positionen) und
    können ohne Engine-Änderung voll implementiert werden.
- **Begründung:** Volle Erklärbarkeit je Komponente, klare Erweiterung nur über
  die Registry, keine Handelslogik in der Engine.
- **Konsequenzen:** Neue Risk-Modelle = Datei in `risk/` + Registrierung +
  Gewicht/Parameter in `risk_rules.toml`; die Engine bleibt unverändert. Die
  Risk Engine trifft **keine** Kauf-/Verkaufsentscheidung und erzeugt **keine**
  Order.

### ADR-028 – Recommendation Engine: Faktoren, No-Trade-Gates, Erklärbarkeit

- **Datum:** 2026-07-09 (Sprint 9)
- **Kontext:** Als letzte fachliche Schicht muss aus Strategie, Score und Risiko
  eine objektive, nachvollziehbare Handlungsempfehlung entstehen – ohne
  Blackbox, ohne automatische Orderausführung, mit vollwertigem „kein Trade".
- **Entscheidung:**
  - Kette `Strategy+Score+Risk → RecommendationEngine → RecommendationReport`;
    konsistent zu den anderen Engines (frozen `models/recommendation.py`,
    generische `Cache`/`Registry`, `AlphaAIError`-Hierarchie, Bau-am-Ende +
    `replace()`). Die Engine ordnet die drei Reports je Hypothese über
    `hypothesis_id` zu.
  - Das Gesamtrating (0..100) ist die gewichtete Summe **sechs** Faktoren
    (Strategie, Score, Risiko, Konsens, Marktqualität, Datenqualität; Gewichte
    aus `[weights]`). Die Engine berechnet Faktoren, Rating und Confidence per
    Basis-Helfer **vorab** und legt sie in den `RecommendationContext` (analog
    zu `ScoreContext.components`); die fünf Modelle transformieren diesen
    Kontext unabhängig voneinander.
  - **No-Trade-Philosophie:** Der Score-Anteil ist bewusst begrenzt und der
    Konsens belohnt **Breite** (voll ab `consensus_full_at` gleichgerichteten
    Strategien). Zusätzlich deckeln **Gates** im `recommendation_model` bei
    erhöhtem Risiko, geringem Konsens, schwacher Datenqualität oder neutraler
    Richtung. So kann ein hoher Score allein **nie** zu BUY/STRONG_BUY führen;
    `WAIT`/`AVOID` sind vollwertige Empfehlungen.
  - **Erklärbarkeit:** `explanation_model` liefert Reasons/Warnings,
    `summary_model` die Kurzfassung, das `recommendation_model` die
    Gate-Begründungen – jede Empfehlung ist vollständig nachvollziehbar.
- **Begründung:** Kombinierte, robuste Entscheidung statt Score-Fixierung; klare
  Erweiterung nur über die Registry; keine Handels-/Orderlogik in der Engine.
- **Konsequenzen:** Neue Recommendation-Modelle = Datei in `recommendation/` +
  Registrierung + Parameter in `recommendation_rules.toml`; die Engine bleibt
  unverändert. Sie liefert ausschließlich `RecommendationResult` – **keine**
  Position, **keine** Order, **keine** Broker-Kommunikation.

### ADR-029 – End-to-End-Integration: Runner, Konsistenz, Validierung

- **Datum:** 2026-07-09 (Sprint 9.5)
- **Kontext:** Die sieben Stufen existierten einzeln und einzeln getestet. Es
  fehlte eine verdrahtete Gesamtkette samt automatischer Konsistenz- und
  End-to-End-Validierung – ohne neue Fachlogik.
- **Entscheidung:**
  - Neues, **rein orchestrierendes** Paket `pipeline/` mit dem
    `IntegrationRunner` (verkettet die bestehenden Engines) und
    `verify_pipeline` (Referenz-/Eindeutigkeits-Konsistenz). Das
    Ergebnisobjekt `PipelineResult` liegt als `frozen`-Modell in `models/`.
  - Der Runner enthält **keine** neue Fachlogik: jede Engine erhält nur
    vorgelagerte Ausgaben (Indikatoren/Muster sind gemeinsame Vorstufen, keine
    Umgehung). Fehlende Daten ergeben ein leeres, aber konsistentes Ergebnis.
  - Validierung über **echte** Szenarien (`tests/scenarios.py`, deterministisch,
    kein Mock) und 180 Integrations-Tests; geprüft werden Konsistenz und die
    Entscheidungs-Invarianten (No-Trade-Gates, „Score allein nie BUY", „hohes
    Risiko deckelt").
  - **Kalibrierungs-Auffälligkeiten** (Richtungs-Semantik der Stufe, Häufigkeit
    von STRONG_BUY, Risiko-Schwellen) werden **dokumentiert** statt behoben –
    Sprint 9.5 ändert bewusst keine Engine und kein Verhalten.
- **Begründung:** Die Gesamtkette muss beweisbar konsistent und regelkonform
  sein, bevor Feinschliff/Kalibrierung erfolgt. Trennung von Integration
  (jetzt) und fachlicher Kalibrierung (später) hält die Änderung risikoarm.
- **Konsequenzen:** `pipeline` ist im Qualitäts-Check und in `pyproject.toml`
  registriert. Die dokumentierten Verbesserungen (u. a. Richtung in
  `RecommendationResult`) sind eigenständige Folge-Sprints; keine Order-/Broker-/
  Dashboard-Funktion entsteht.

### ADR-030 – Trennung von Direction und RecommendationStrength

- **Datum:** 2026-07-09 (Sprint 9.6)
- **Kontext:** Der Validierungssprint 9.5 zeigte, dass die Empfehlungsstufe
  (STRONG_BUY/BUY/…) **Richtung und Stärke vermischte**: ein starkes bärisches
  Setup wurde als „STRONG_BUY" dargestellt. „BUY" beschreibt zugleich Richtung
  **und** Güte – fachlich falsch.
- **Entscheidung:**
  - `RecommendationResult` trägt **zwei unabhängige** Informationen:
    `direction` (:class:`Direction` – LONG/SHORT/NEUTRAL, ausschließlich die
    Richtung, abgeleitet aus der Strategie-Hypothese) und
    `recommendation_strength` (:class:`RecommendationStrength` –
    VERY_HIGH/HIGH/MEDIUM/LOW/REJECT, ausschließlich die Qualität).
  - Die Stärke enthält **kein** BUY/SELL/LONG/SHORT mehr; das ist per Test
    abgesichert. Ein bärisches Setup ist ``SHORT`` mit ggf. hoher Stärke.
  - Es wurden **ausschließlich** Domänenmodelle, Mappings (level→strength),
    Validierungen, Config-Schlüssel und Dokumentation angepasst. Die
    **Bewertungslogik** (Faktoren, Rating, Gates, Schwellenwerte) ist
    **unverändert** – die Rating-Werte sind identisch zu 9.5.
- **Begründung:** Fachlich korrekte, missverständnisfreie Empfehlung; die
  Richtung ist nun explizit und die Güte richtungsneutral.
- **Konsequenzen:** Keine neue Engine, keine neue Logik, keine neuen
  Handelsregeln. Öffentliches Feld `recommendation_level` heißt jetzt
  `recommendation_strength`; zusätzlich existiert `direction`. Downstream
  (Dashboard etc., später) nutzt beide Felder getrennt.
