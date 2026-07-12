# Market Discovery (Automatische Markt-Durchsuchung)

_Wird laufend gepflegt._ Diese Datei beschreibt das Market-Discovery-Framework aus
Sprint 15. AlphaAI ist damit **nicht mehr auf Watchlists angewiesen**: das System
durchsucht den gesamten konfigurierten Markt selbstständig, filtert ungeeignete
Werte **vor** der vollständigen Analyse und präsentiert am Ende ausschließlich die
objektiv besten Chancen. Es **berechnet niemals** Indikatoren, Muster, Strategien,
Scores, Risiken oder Empfehlungen – es nutzt ausschließlich bereits vorhandene
Ergebnisse.

## Idee in einem Satz

Der Benutzer gibt keine Aktien mehr vor: AlphaAI lädt automatisch das Universum,
wirft ungeeignete Kandidaten heraus, bewertet den Rest mit der **bestehenden**
Pipeline und zeigt morgens die relevantesten Opportunities des Tages mit
vollständiger Begründung.

## Kette

```
Market Universe (automatisch geladen)
        ↓  Discovery Engine
Candidate Filter (Vorfilter: Liquidität/Volumen/Historie/…)
        ↓  je verbleibendem Wert: bereits vorhandene Ergebnisse (injiziert)
Scanner → Indicator → Pattern → Strategy → Score → Risk → Recommendation → Analytics
        ↓  Market Intelligence (bestehend, unverändert)
Branchen-Ausgleich → Statistik
        ↓
Discovery Report → Dashboard („Market Discovery")
```

Die Discovery Engine **importiert nichts** aus der Pipeline: die vorhandenen
Ergebnisse je Wert und der Market-Intelligence-Schritt werden **injiziert**
(Duck-Typing). Sie berechnet nichts selbst und verändert keine bestehende Engine.

## Bausteine

Paket `market_discovery/` (Subsystem, wie `market_intelligence/` – nur der
Zyklenprüfung unterworfen; importiert ausschließlich `models`/`core`):

| Modul | Aufgabe |
|---|---|
| `universe_loader.py` | Lädt Werte je registriertem Markt über eine **injizierte** Symbol-Quelle, vervollständigt Stammdaten, dedupliziert. |
| `market_universe.py` | Struktur-Operationen am Universum (Zusammenführen, Deduplizieren, Vervollständigen). |
| `candidate_filter.py` | Vorfilter: entfernt ungeeignete Werte anhand vorhandener Stammdaten (Grenzwerte aus der Regeldatei). |
| `candidate.py` | Baut aus `MarketSymbol` + vorhandenen Reports einen `MarketCandidate`; wandelt die bewertete `Opportunity` samt Stammdaten in eine `DiscoveryOpportunity` um. |
| `sector_balancer.py` | Branchen-Ausgleich (konfigurierbar, keine festen Limits) gegen einseitige Ergebnislisten. |
| `market_statistics.py` | Kennzahlen des Laufs (Anzahlen, Durchschnitte, Top-Branchen/Märkte). |
| `discovery_engine.py` | Orchestrierung (Vorfilter → Kandidaten → **injizierter** Intelligence-Schritt → Ausgleich → Statistik → Report). |
| `discovery_cache.py` | `DiscoveryCache` (FIFO, Spezialisierung von `core.cache.Cache`). |

Engine-Anbindung (`engines/`): `market_discovery_engine.py` (öffentliche Engine +
Regel-Laden + Cache/Timing), `market_discovery_registry.py` (Registry der Märkte –
einzige Erweiterungsstelle), `market_discovery_cache.py` und
`market_discovery_result.py` (Re-Exporte).

## Unterstützte Märkte

NYSE, NASDAQ, S&P 500, NASDAQ 100, Russell 2000, DAX, MDAX, SDAX, TecDAX,
Euro Stoxx 50. **Weitere Märkte** werden einfach als
:class:`~models.market_discovery.MarketDefinition` in der Registry ergänzt – die
Engine bleibt unverändert (Open/Closed).

## Vorfilter (Candidate Filter)

Vor der vollständigen Analyse werden ungeeignete Werte entfernt – anhand
**vorhandener** Stammdaten, nicht durch Berechnung:

- Mindestkurs, Mindestvolumen, Mindest-Liquidität (Umsatz), Mindest-Historie,
- gültige Kurse, Handelbarkeit, keine Delistings, keine Penny Stocks
  (konfigurierbar).

Alle Grenzwerte stehen ausschließlich in `knowledge/market_discovery_rules.toml`.
Jeder verworfene Wert wird mit **Grund** im Report festgehalten.

## Branchen-Ausgleich (Sector Balancing)

Verhindert eine einseitige Ergebnisliste: Sind viele Werte derselben Branche
gleichzeitig stark bewertet, zieht der Ausgleich – nach `max_streak` direkt
aufeinanderfolgenden Werten derselben Branche – nach Möglichkeit eine andere
Branche vor. Vollständig konfigurierbar (`[balancing]`), **keine festen
Branchenlimits**; ohne Aktivierung bleibt die reine Score-Reihenfolge erhalten.

## Discovery Report

Enthält: Anzahl analysierter Aktien, Anzahl verworfener Kandidaten, Anzahl
vollständiger Analysen, Anzahl LONG/SHORT/WATCH, Top Opportunities, Top Branchen,
Top Märkte sowie Durchschnitt von Score/Risiko/Confidence. Jede
`DiscoveryOpportunity` trägt: Ticker, Unternehmen, Branche, **Land**, Börse,
Direction, Recommendation Strength, Confidence, Risk, Opportunity Score, Ranking,
Summary, Reasons, Warnings, Analytics-/Backtest-/Paper-Trading-Summary und
Timestamp. Alle Typen sind unveränderlich (`frozen`).

## Dashboard

Neue Seite **Market Discovery** (additiv über Router/Registry; die
`DashboardEngine` bleibt unverändert): Top Opportunities, Gesamtmarktübersicht,
Branchenübersicht, Marktübersicht sowie ein Ranking mit Suche und Filtern (Markt/
Richtung). Das Dashboard **visualisiert ausschließlich** den DiscoveryReport –
**keine** Berechnung im Frontend.

## Validierung

Leeres Universum (Report ungültig, aber ohne Exception), unbekannte Märkte
(übersprungen mit Warnung), ungültige Symbole/fehlende Ticker (übersprungen),
doppelte Kandidaten (dedupliziert mit Warnung), ungültige Rankings/Branchen/Märkte
werden vom bestehenden Intelligence-/Statistik-Schritt abgefangen.

## Performance

Der Vorfilter läuft **vor** der vollständigen Analyse – ungeeignete Werte werden
gar nicht erst bewertet (keine unnötigen Berechnungen). Die Architektur ist auf
spätere Parallelisierung vorbereitet (klar getrennte, zustandslose Schritte),
ohne dass jetzt bereits parallelisiert wird.

## Erweitern

- **Neuer Markt:** eine `MarketDefinition` in
  `engines/market_discovery_registry.py` ergänzen. Die Engine bleibt unverändert.
- **Datenanbindung:** die reale Symbol-Quelle und die Quelle der vorhandenen
  Ergebnisse werden über `discover(..., symbol_source=…, analysis_provider=…)`
  injiziert – ohne Änderung am Framework.
- **Grenzwerte/Ausgleich:** ausschließlich über
  `knowledge/market_discovery_rules.toml`.

## Tests

Umfassende Abdeckung für Universe-Loader, Discovery-Engine, Candidate-Filter,
Sector-Balancer, Statistik, Cache, Registry, Kandidaten-Umwandlung,
End-to-End-Szenarien und die Dashboardseite.
