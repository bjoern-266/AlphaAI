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

### ADR-031 – Backtesting als rein bewertendes Subsystem hinter der Pipeline

- **Datum:** 2026-07-10 (Sprint 10)
- **Kontext:** Die Qualität der bestehenden AlphaAI-Empfehlungen sollte an
  historischen Daten messbar werden, **ohne** die Fachlogik zu verändern und
  **ohne** Auto-Trading einzuführen.
- **Entscheidung:**
  - Das Backtesting hängt **nur hinten** an die bestehende Pipeline an: der
    `HistoricalRunner` ruft den unveränderten `IntegrationRunner` fensterweise
    auf (`frame.iloc[:i+1]`), sodass an jedem Punkt **nur** vergangene Kerzen
    sichtbar sind (kein Look-Ahead). Keine Engine wird angefasst.
  - `backtesting/` ist ein **Subsystem** (wie `pipeline/`), keine Plugin-Familie
    mit Unabhängigkeitsprüfung: die Hilfsmodule (`historical_runner`,
    `trade_simulator`, `performance_metrics`, `equity_curve`, `statistics`,
    `benchmark`) dürfen zusammenarbeiten. Es ist in `quality_check.py` nur der
    Zyklenprüfung unterworfen (0 Zyklen).
  - Die messbaren Kennzahlen sind als **Registry-Plugins** organisiert
    (`performance_model`, `drawdown_model`, `ratio_model`, `benchmark_model`);
    neue Kennzahlgruppen kommen ausschließlich über `backtest_registry.py` hinzu,
    die Engine bleibt unverändert (Open/Closed).
  - **Trades werden nur simuliert** (kein Broker, keine Order). Stop/Take-Profit/
    Stückzahl kommen aus der Risk Engine; alle Konto-/Risikowerte stammen
    ausschließlich aus `settings.toml`. Fractional Shares werden unterstützt.
    Trifft eine Kerze Stop **und** Take-Profit, gilt konservativ der Stop.
  - **Sharpe/Sortino/Calmar** sind **vorbereitet**: implementiert, aber nicht
    annualisiert/kalibriert und `None` bei zu wenig Daten (analog zum
    „News"-Risiko). Der Profit Factor ist ohne Verluste bewusst `inf`.
- **Begründung:** Objektive, nachvollziehbare Bewertung ohne Eingriff in die
  Entscheidungslogik; die Trennung „Signal (bestehende Empfehlung) →
  Simulation → Kennzahl" hält das Framework prüfbar und erweiterbar.
- **Konsequenzen:** Kein Dashboard, keine Broker-API, kein Paper-Trading, keine
  automatische Orderausführung, keine neue Handelsregel. `engines/` importiert
  über `backtest_engine.py` das `pipeline`-Subsystem (kein Zyklus). Kalibrierung
  der vorbereiteten Kennzahlen ist im `VALIDATION_REPORT.md` als offener Schritt
  festgehalten.

### ADR-032 – Paper Trading als simuliertes Portfolio hinter der Pipeline

- **Datum:** 2026-07-10 (Sprint 11)
- **Kontext:** Die bestehenden Empfehlungen sollten unter (simulierten)
  Live-Bedingungen mit einem fortlaufenden Portfolio bewertbar werden – **ohne**
  echte Orders, **ohne** Broker-Anbindung und **ohne** Eingriff in die Fachlogik.
- **Entscheidung:**
  - Wie das Backtesting hängt Paper Trading **nur hinten** an die bestehende
    Pipeline: der `PaperRunner` ruft den unveränderten `IntegrationRunner`
    tagweise auf (`frame.iloc[:i+1]`, kein Look-Ahead). Keine Engine wird
    angefasst, keine Empfehlung verändert.
  - `paper_trading/` ist ein **Subsystem** (wie `pipeline/`/`backtesting/`), in
    `quality_check.py` nur der Zyklenprüfung unterworfen. Die Kennzahlgruppen
    (Statistik, Performance) sind **Registry-Plugins**; neue kommen ausschließlich
    über `paper_trading_registry.py` hinzu (Open/Closed).
  - **Ergebnis-/Snapshot-Typen sind unveränderlich** (`frozen`); Positionen
    werden über `dataclasses.replace` fortgeschrieben. Das **Portfolio** und das
    **Journal** sind bewusst zustandsbehaftete Manager (analog zu Engines/Caches)
    – sie sind keine „Ergebnisobjekte" und daher nicht `frozen`.
  - **Order-Management** kennt `OPEN/CLOSE/CANCEL/EXPIRE`; gültig sind nur
    Übergänge einer offenen Position. Validierung verhindert doppelte Positionen
    derselben Empfehlung, negative Größen, ungültige Preise/Zeitstempel und
    ungültige Statuswechsel (`PaperTradingValidationError`).
  - **Trades werden nur simuliert.** Stop/Take-Profit/Stückzahl kommen aus der
    Risk Engine; alle Konto-/Risikowerte stammen ausschließlich aus
    `settings.toml`. Fractional Shares werden unterstützt (Abrunden nur bei
    `fractional_shares = false`). Trifft ein Tag Stop **und** Take-Profit, gilt
    konservativ der Stop.
  - Der **Trailing Stop** ist **vorbereitet** (implementiert, aber per Default
    inaktiv über `trailing_distance = 0.0`).
- **Begründung:** Objektive, vollständig nachvollziehbare Bewertung der
  bestehenden Entscheidungen unter Portfolio-Bedingungen; die Trennung „Signal
  (bestehende Empfehlung) → Order/Position → Kennzahl" hält das Framework prüfbar
  und erweiterbar.
- **Konsequenzen:** Kein Dashboard, keine Broker-API, keine echten Orders, keine
  automatische Orderausführung, keine neue Handelsregel. `engines/` importiert
  über `paper_trading_engine.py` das `pipeline`-Subsystem (kein Zyklus).

### ADR-033 – Analytics als rein auswertendes Subsystem über den Ergebnissen

- **Datum:** 2026-07-11 (Sprint 12)
- **Kontext:** AlphaAI sollte beginnen, seine eigenen Entscheidungen automatisch
  auszuwerten – **objektiv**, **reproduzierbar** und **ohne** Eingriff in die
  Fachlogik, ohne neue Empfehlungen und ohne Machine Learning.
- **Entscheidung:**
  - Das Analytics-Framework **liest** ausschließlich bestehende
    `BacktestReport`/`PaperTradingReport` und schreibt nichts zurück. Es bewertet
    keine Trades und trifft keine Handelsentscheidung – es erzeugt nur Statistiken.
  - `analytics/` ist ein **Subsystem** (wie `pipeline/`/`backtesting/`/
    `paper_trading/`), in `quality_check.py` nur der Zyklenprüfung unterworfen.
    Die zehn Analysen sind **Registry-Plugins**; neue kommen ausschließlich über
    `analytics_registry.py` hinzu – die Engine wird dafür **nie** geändert
    (Open/Closed). Die Modelle sind **unabhängig** voneinander (kein Modell
    importiert ein anderes; gemeinsame Bausteine liegen in `aggregation.py`).
  - **Normalisierung:** Backtest- und Paper-Trades werden in einen einheitlichen
    `AnalyticsTrade` überführt. Analyse-Dimensionen werden **nachvollziehbar** aus
    den vorhandenen Daten abgeleitet: Strategie aus der `recommendation_id`,
    Risiko-Level und Score aus den `reasons`. Fehlt eine Information, gilt
    ``"unbekannt"``/``None`` – es werden **keine** Daten erfunden. Pattern-/
    Markt-Dimensionen sind label-basiert und damit erweiterbar, sobald künftige
    Trades entsprechende Labels tragen (ohne Engine-Änderung).
  - **Reproduzierbarkeit:** alle Kennzahlen stammen aus `aggregation.py` (eine
    Quelle der Definitionen); der Drawdown wird auf einer Kapitalkurve
    ``base_capital + kumulierter PnL`` gemessen (``base_capital`` aus der Regel-
    datei). Keine Blackbox.
  - **Ergebnis-Typen sind unveränderlich** (`frozen`); alle Kennzahlen liegen im
    `AnalyticsResult` fertig berechnet vor, sodass ein späteres Dashboard nur
    visualisieren muss (keine Geschäftslogik im Dashboard).
- **Begründung:** Objektive, vollständig nachvollziehbare Selbstauswertung der
  bestehenden Entscheidungen; die klare Trennung „Ergebnisse → Normalisierung →
  Kennzahl" hält das Framework prüfbar und beliebig erweiterbar.
- **Konsequenzen:** Keine Dashboard-Komponenten, keine Broker-API, keine
  Handelslogik, keine neuen Empfehlungen, keine ML-Komponenten. `engines/`
  importiert über `analytics_engine.py` das `analytics`-Subsystem und liest die
  Modelle `models.backtest`/`models.paper_trading` (kein Zyklus).

### ADR-034 – Dashboard als reine Presentation Layer (keine Berechnung)

- **Datum:** 2026-07-11 (Sprint 13)
- **Kontext:** AlphaAI brauchte eine Oberfläche („Command Center"), die die
  bereits vorhandenen Ergebnisse sichtbar macht – **ohne** die Gefahr, dass in
  der UI heimlich Fachlogik entsteht (Scores/Risiken/Empfehlungen/Kennzahlen neu
  berechnet werden). Zusätzlich ist Streamlit in der Umgebung **nicht**
  installiert, die Logik muss aber vollständig testbar bleiben.
- **Entscheidung:**
  - Das Dashboard ist **ausschließlich** Presentation Layer: es **liest** die
    bestehenden Reports (`ReportBundle`) und **zeigt** sie an. Es **berechnet
    niemals** Daten und enthält **keinerlei** Geschäftslogik. Fehlt ein Wert im
    Report, bleibt er `None` und wird als Platzhalter (`—`) angezeigt – **keine**
    Ersatzberechnung. Auto-Refresh lädt **nur** neue Reports und startet nie eine
    Berechnung.
  - Architektur `Reports → DashboardEngine → DashboardViewModel → Widgets →
    DashboardView → Streamlit`. `dashboard/` ist ein **Subsystem** (wie
    `analytics/`), in `quality_check.py` nur der Zyklenprüfung unterworfen;
    `models/dashboard.py` gehört zur Entities-Schicht (importiert nur
    `models.analytics`).
  - **Open/Closed:** die 26 Widgets sind **Registry-Plugins** und **unabhängig**
    (kein Widget importiert ein anderes; gemeinsame Bausteine in
    `widgets/common.py`). Neue Widgets kommen ausschließlich über
    `widget_registry.py`, neue Seiten ausschließlich über `router.py`, das
    Aussehen ausschließlich über `theme.py` – die `DashboardEngine` wird dafür
    **nie** geändert.
  - **Aussehen zentralisiert:** sämtliche Farben/Schriften/Abstände/Rahmen/
    Animationen/Icons/Materialien liegen im `theme.py` („Dark Carbon"); im
    übrigen Code gibt es **keine** hartcodierten Gestaltungswerte. Anzeige-
    einstellungen (`settings.toml`) enthalten **keine** Handelsparameter.
  - **Testbarkeit:** der Streamlit-Import ist auf `render.py`/`app.py` beschränkt
    und **lazy** (in den Funktionen, `# pragma: no cover`). Die gesamte übrige
    Logik ist Streamlit-frei und wird ohne installiertes Streamlit getestet.
  - **Robustheit:** Anzeigetypen sind `frozen`; der veränderliche
    `DashboardState` sichert sich per `snapshot()`/`restore()` (Zustand geht nie
    verloren). Lade-/Fehlerzustände werden angezeigt; ein Fehler eines einzelnen
    Widgets wird isoliert als Platzhalter dargestellt – **keine Exceptions im
    Frontend**.
- **Begründung:** Die strikte Trennung „Reports (Fakten) → View Model (Ablesen)
  → Widget (Formatieren) → Streamlit (Zeichnen)" macht es strukturell unmöglich,
  in der UI zu rechnen, hält das Dashboard prüfbar und beliebig erweiterbar und
  entkoppelt es vollständig von Streamlit.
- **Konsequenzen:** Keine Broker-API, keine Handelslogik, keine neuen Kennzahlen,
  keine ML-Komponenten im Dashboard. `dashboard/` liest die bestehenden
  `models.*`-Reports und die Ergebnistypen; es entsteht kein Import-Zyklus, und
  keine bestehende Engine wird verändert.

### ADR-035 – Market Intelligence als priorisierendes Subsystem (kein neues Bewertungssystem)

- **Datum:** 2026-07-12 (Sprint 14)
- **Kontext:** AlphaAI sollte erstmals den gesamten Markt betrachten und die
  objektiv besten Chancen priorisieren – **ohne** eine neue Handelsregel oder ein
  neues Bewertungssystem einzuführen und **ohne** bestehende Ergebnisse zu ändern.
- **Entscheidung:**
  - Das Market-Intelligence-Framework **liest** je Aktie die bereits vorhandenen
    Reports (Empfehlung, Risiko, Analytics, Backtesting, Paper Trading), gebündelt
    als `MarketCandidate`, und schreibt nichts zurück. Es trifft keine
    Handelsentscheidung.
  - **Kein neues Bewertungssystem:** der `opportunity_score` ist die **gewichtete
    Zusammenfassung** von fünf **bestehenden** Kennzahlen (Overall Rating,
    Risiko-Faktor, drei Win Rates). Jede Komponente ist ein **Registry-Plugin**
    (`BaseOpportunityModel`); neue kommen ausschließlich über
    `market_intelligence_registry.py` hinzu – die Engine wird dafür **nie** geändert
    (Open/Closed). Die Modelle sind **unabhängig** voneinander.
  - **Regeln nur aus TOML:** alle Gewichte und Parameter stehen in
    `knowledge/market_intelligence_rules.toml`; die aktivierten Gewichte müssen 1.0
    ergeben (sonst Regel-Ladefehler). Fehlt eine Quelle, wird ihr Beitrag
    ausgelassen und über die verbleibenden Gewichte normalisiert – es wird nichts
    erfunden. Richtung/Stärke/Confidence/Rating/Risiko kommen unverändert aus der
    Empfehlung; ohne Empfehlung gilt „Watch" (neutral, Score 0).
  - **Transparenz:** jede Chance trägt ihre Komponenten-Scores und eine
    Herleitung (Faktoren, Risiken, „warum nicht höher") – keine Blackbox.
  - `market_intelligence/` ist ein **Subsystem** (wie `analytics/`), in
    `quality_check.py` nur der Zyklenprüfung unterworfen. `models/opportunity.py`
    (Entities) importiert nur andere Modelle. Alle Ergebnistypen sind `frozen`.
  - **Dashboard:** die neue Seite „Market Intelligence" wird **additiv** über
    Router/Registry angebunden; die `DashboardEngine` bleibt unverändert und
    **visualisiert ausschließlich** den `OpportunityReport` (keine Berechnung).
- **Begründung:** Die Priorisierung entsteht vollständig aus bereits geprüften,
  reproduzierbaren Signalen; die klare Trennung „Reports → Bewertungsmodell →
  Opportunity → Ranking" hält das Framework prüfbar, transparent und erweiterbar,
  ohne die bestehende Fachlogik zu berühren.
- **Konsequenzen:** Keine neue Handelsregel, keine Broker-API, keine Echtgeldorders,
  keine ML-Komponenten. `engines/` importiert über `market_intelligence_engine.py`
  das `market_intelligence`-Subsystem und liest die bestehenden `models.*`-Reports
  (kein Zyklus); keine bestehende Engine wird verändert.

### ADR-036 – Market Discovery als durchsuchendes Subsystem (Pipeline injiziert)

- **Datum:** 2026-07-12 (Sprint 15)
- **Kontext:** AlphaAI sollte **nicht mehr auf Watchlists angewiesen** sein: das
  System sollte den gesamten konfigurierten Markt selbstständig durchsuchen,
  ungeeignete Werte vorab filtern und die besten Chancen priorisieren – **ohne**
  neue Scores/Strategien/Pattern/Risk-Regeln und **ohne** eine bestehende Engine
  zu verändern.
- **Entscheidung:**
  - Das Discovery-Framework lädt das Universum, filtert Kandidaten und
    priorisiert über den **bestehenden** Market-Intelligence-Schritt. Es
    **berechnet niemals** Indikatoren/Muster/Strategien/Scores/Risiken/
    Empfehlungen.
  - **Injektion statt Import:** die Werte je Markt (`symbol_source`), die bereits
    vorhandenen Ergebnisse je Wert (`analysis_provider`) und der
    Market-Intelligence-Schritt werden dem Subsystem **injiziert** (Duck-Typing).
    Dadurch importiert `market_discovery/` ausschließlich `models`/`core` – kein
    Import aus `engines`, kein Import-Zyklus, saubere Schichtung.
  - **Vorfilter vor der Analyse:** ungeeignete Werte (Liquidität, Volumen,
    Historie, gültige Kurse, Handelbarkeit, Delisting, Penny Stocks) werden **vor**
    der vollständigen Bewertung entfernt (Performance; keine unnötigen
    Berechnungen). Grenzwerte ausschließlich aus
    `knowledge/market_discovery_rules.toml`; jeder verworfene Wert wird mit Grund
    festgehalten.
  - **Branchen-Ausgleich** verhindert einseitige Ergebnislisten – vollständig
    konfigurierbar, **keine festen Branchenlimits**; ohne Aktivierung bleibt die
    Score-Reihenfolge erhalten.
  - **Open/Closed:** unterstützte Märkte sind `MarketDefinition`-Registry-Einträge;
    neue Märkte kommen ausschließlich über `market_discovery_registry.py` hinzu –
    die Engine bleibt unverändert. Alle Ergebnistypen sind `frozen`.
  - Die Architektur ist auf spätere **Parallelisierung** vorbereitet (zustandslose,
    getrennte Schritte), ohne dass jetzt bereits parallelisiert wird.
  - **Dashboard:** die neue Seite „Market Discovery" wird additiv über
    Router/Registry angebunden; die `DashboardEngine` bleibt unverändert und
    **visualisiert ausschließlich** den `DiscoveryReport`.
- **Begründung:** Die Injektion von Pipeline und Intelligence hält das Subsystem
  vollständig entkoppelt und prüfbar; der Vorfilter vor der Analyse macht große
  Universen effizient verarbeitbar; die klare Schritt-Trennung ermöglicht spätere
  Parallelisierung, ohne die bestehende Fachlogik zu berühren.
- **Konsequenzen:** Keine neuen Scores/Strategien/Pattern/Risk-Regeln, keine
  Broker-API, keine Echtgeldorders. `engines/` verdrahtet über
  `market_discovery_engine.py` das `market_discovery`-Subsystem mit der
  `MarketIntelligenceEngine`; keine bestehende Engine wird verändert. Nach der
  Discovery trifft der Benutzer die Handelsentscheidung selbst.

### ADR-037 – Live Operations als orchestrierendes Subsystem (Jobs/Uhr injiziert)

- **Datum:** 2026-07-12 (Sprint 16)
- **Kontext:** AlphaAI sollte als **produktives tägliches Analyse-System**
  arbeiten: der Benutzer startet es, danach laufen alle Marktanalysen automatisch
  (keine manuellen Discovery-/Scanner-Läufe). Ziel war **praktische Nutzbarkeit**,
  keine neue Architektur – und weiterhin **niemals** Orders.
- **Entscheidung:**
  - Die Operations Platform erkennt automatisch die Marktzeiten (Marktuhr), plant
    die Jobs (Scheduler) und startet fällige Jobs selbst. Sie **berechnet nichts**
    und trifft **keine** Handelsentscheidung – sie **orchestriert** die bestehende
    Pipeline.
  - **Injektion statt Import:** die eigentlichen Jobs
    (`jobs={job_type: callable}`) und die Uhr (`clock`) werden dem
    `OperationsEngine` injiziert (Duck-Typing). Dadurch importiert `operations/`
    ausschließlich `models`/`core` – kein Import aus `engines`, kein Zyklus, saubere
    Schichtung; keine bestehende Engine wird verändert.
  - **Marktzeiten & DST:** Marktphasen je Markt sind in der Zeitzone des Marktes
    konfiguriert; Sommer-/Winterzeit wird automatisch über die IANA-Zeitzonen
    (`zoneinfo`) berücksichtigt. Alle Zeiten/Zeitpläne/Schwellen stehen
    ausschließlich in `knowledge/operations_rules.toml`.
  - **Robustheit:** die Job-Queue lässt nur **ein** Discovery gleichzeitig zu und
    verhindert parallele Vollanalysen; der Job-Runner isoliert Fehler, sodass ein
    Absturz den Scheduler nie blockiert (automatische Wiederaufnahme im nächsten
    Takt). Alle Report-Typen sind `frozen`.
  - **UI-Unabhängigkeit / API-Vorbereitung:** der `OperationReport` enthält nur
    Daten; Desktop-Dashboard, spätere REST-API und mobile Apps nutzen denselben
    Report (keine doppelte Geschäftslogik). Die Dashboard-Seite „Live Operations"
    wird **additiv** über Router/Registry angebunden; die `DashboardEngine` bleibt
    unverändert und visualisiert nur den Report.
  - **Open/Closed:** Job-Arten sind `JobDefinition`-Registry-Einträge; neue Arten
    kommen ausschließlich über `operations_registry.py` hinzu – die Engine bleibt
    unverändert. Parallelisierung und REST sind vorbereitet, aber bewusst noch
    nicht implementiert (Ziel: höchster praktischer Nutzen, keine theoretischen
    Frameworks).
- **Begründung:** Die Injektion von Jobs und Uhr hält das Subsystem entkoppelt und
  vollständig testbar (feste Uhr, Fake-Jobs); die konfigurierten Marktzeiten mit
  automatischer DST-Behandlung und die robuste Job-Queue machen AlphaAI unmittelbar
  im Börsenalltag einsetzbar, ohne die bestehende Fachlogik zu berühren.
- **Konsequenzen:** Keine neuen Strategien/Pattern/Scores/Risk-Regeln, keine
  Broker-API, keine automatische Orderausführung. `engines/` verdrahtet über
  `operations_engine.py` das `operations`-Subsystem; die realen Jobs werden beim
  Start injiziert. Der Benutzer erhält ohne Eingaben eine belastbare
  Entscheidungsgrundlage und trifft die Handelsentscheidung selbst.

### ADR-038 – Production Backend & REST-API als reine Auslieferungsschicht (Reports injiziert/gespeichert)

- **Datum:** 2026-07-12 (Sprint 17)
- **Kontext:** AlphaAI sollte als **produktiver Backend-Dienst** laufen und alle
  Frontends (Desktop-Dashboard, spätere Android-App) über **eine** Schnittstelle
  bedienen – ohne doppelte Geschäftslogik, ohne Änderung bestehender Engines und
  weiterhin **niemals** mit Orderausführung.
- **Entscheidung:**
  - **Neue Schicht `application/`** (Service Layer) mit klar getrennten Bausteinen
    (`exceptions`, `serialization`, `repositories`, `responses`, `services`,
    `health`, `authentication`, `api`). Sie **liest** ausschließlich vorhandene
    Reports, berechnet nichts und trifft keine Handelsentscheidung.
  - **Injektion statt Import:** `application/` importiert nur `models`/`core`; der
    Operations-Taktgeber und zusätzliche Fach-Report-Quellen werden dem
    `BackgroundService`/der `ApplicationEngine` injiziert (Duck-Typing). Die
    `ApplicationEngine` (in `engines/`) ist der einzige Composition Root, der
    Engines und `application` kennt – so entstehen **keine Import-Zyklen** und
    keine bestehende Engine wird verändert.
  - **Produktionsgeeignete Persistenz:** `ReportStore` auf **SQLite** (eingebettet,
    transaktional, dauerhaft auf Platte). Keine temporären Dateien, keine reine
    In-Memory-Lösung; Retention je Report-Art; der neueste Eintrag je Art ist der
    „letzte erfolgreiche Scan", der Neustarts übersteht.
  - **Verlustfreie, generische Serialisierung:** ein einziger rekursiver
    Serialisierer wandelt beliebige (frozen) Reports in JSON – kein Fachwissen über
    einzelne Felder, damit stabil bei neuen Report-Feldern.
  - **Framework-unabhängige REST-API:** Routing/Request/Response/Cache sind ohne
    Web-Framework umgesetzt und vollständig testbar; ein **dünner FastAPI-Adapter**
    (lazy import, GZip) bindet HTTP an – dieselbe Trennung wie beim streamlit-freien
    Dashboard. Alle Antworten sind JSON in einer einheitlichen `ApiEnvelope`,
    versioniert unter `/api/v1`.
  - **Caching mit Auto-Invalidierung:** Antworten werden pro
    `(Methode, Pfad, Query)` **an die Speicher-Revision gebunden** zwischen-
    gespeichert; ein neuer Report ändert die Revision und liefert automatisch den
    frischen Stand – nie ein veralteter Scan.
  - **Vorbereitete Zugriffskontrolle:** `AuthPolicy`-Vertrag; Standard
    `LocalOnlyPolicy` (nur lokaler Host). Keine Cloud, keine Benutzerverwaltung,
    keine Registrierung – aber erweiterbar (Open/Closed).
  - **Robustheit/Recovery:** Hintergrunddienst kapselt jeden Schritt; Fehler werden
    gezählt und protokolliert, der Takt läuft weiter, der letzte gute Scan bleibt
    erhalten. Fehler stoppen den Dienst nie dauerhaft.
  - **Open/Closed:** neue Report-Arten kommen ausschließlich über
    `application_registry.py` hinzu; die Engine/API bleiben unverändert.
- **Begründung:** Eine dünne, lesende Auslieferungsschicht über einer dauerhaften
  Persistenz macht AlphaAI produktiv betreibbar und für Sprint 18 (Android, nur
  HTTP) vollständig vorbereitet, ohne die bestehende Fachlogik zu berühren. Die
  Framework-Unabhängigkeit hält die gesamte Logik testbar (FastAPI optional).
- **Konsequenzen:** Keine neuen Strategien/Pattern/Scores/Risk-Regeln, keine
  Broker-API, keine automatische Orderausführung. `engines/` verdrahtet über
  `application_engine.py` die `application`-Schicht; Operations-Taktgeber und
  Report-Quellen werden beim Start injiziert. Sprint 17 bildet das **endgültige
  Backend**; Sprint 18 entwickelt ausschließlich die Android-App und benötigt
  keine Engine-Änderungen. Die Handelsentscheidung trifft weiterhin der Benutzer.
