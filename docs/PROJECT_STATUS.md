# Projektstatus

_Wird nach jedem Sprint automatisch aktualisiert._

- **Datum:** 2026-07-08
- **Aktueller Sprint:** Sprint 2 – Data Layer
- **Status:** ✅ Abgeschlossen

## Was ist vorhanden

### Fundament (Sprint 1)

- Modulare Projektstruktur, Konfiguration, Logging, Fehlerklassen,
  Wissensbasis, Dokumentation, Basistests.

### Data Layer (Sprint 2)

- **Anfrage/Ergebnis:** `MarketRequest` (unveränderlich, mit Cache-Schlüssel)
  und `MarketResult` (kanonisches OHLCV-Schema inkl. Adjusted Close/Volume,
  Status, Metadaten, Fehler).
- **Provider:** `BaseProvider`-Schnittstelle und implementierter
  `YahooProvider` (yfinance, mit injizierbarer Download-Funktion). Vorbereitet:
  `finnhub`, `polygon`, `alphavantage`, `iex` (per Factory bekannt, ohne
  Implementierung).
- **Repository:** `MarketRepository` kapselt Provider, Cache und Validator.
  `repository_factory` verdrahtet alles aus der Konfiguration.
- **Engine:** `MarketDataEngine` als oberste, fachnahe Zugriffsschicht (kennt
  ausschließlich das Repository).
- **Cache:** `TTLCache` mit kategoriespezifischer TTL (historisch, intraday,
  Tickerlisten), injizierbare Uhr.
- **Validator:** Prüft NaN, nicht-positive Preise, doppelte/unsortierte
  Zeitstempel, fehlende Kerzen (Warnung) und ungültige Symbole.
- **Universe:** `config/universe.toml` + Loader für DAX, MDAX, SDAX, TecDAX,
  S&P 500, Nasdaq-100, Russell 2000 sowie vorbereitetes ETF-Universum.
- **Konfiguration:** neuer `[data]`-Bereich (Provider, Intervall, Zeitraum,
  Cache-TTLs) – alles ausschließlich aus TOML.
- **Tests:** 68 Tests (pytest), Ruff- und Black-konform.

## Was ist bewusst NICHT vorhanden

- Kein Scanner.
- Keine Indikatoren (EMA, RSI, FVG …).
- Keine Muster-/Strategielogik, keine Scores.
- Keine Handelsentscheidungen.

Diese Teile folgen ab Sprint 3 (siehe `ROADMAP.md`).

## Qualitätsnachweis (Sprint 2)

| Prüfung | Ergebnis |
|---|---|
| pytest  | 68 Tests bestanden |
| Ruff    | keine Beanstandungen |
| Black   | konform |

## Nächster Schritt

Warten auf Freigabe für **Sprint 3 – Analyse-Engines** (technische Indikatoren
auf Basis der Data Layer).
