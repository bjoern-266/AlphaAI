# AlphaAI Android App (Sprint 18)

Die Android-App ist ab Sprint 18 die **primäre Benutzeroberfläche** von AlphaAI.
Der Benutzer öffnet morgens ausschließlich die App; alle Marktanalysen laufen
automatisch im Backend. Die App **konsumiert ausschließlich die REST-API** und
enthält **keine** Geschäftslogik.

## Grundsätze

- **Reiner REST-Client:** ausschließlich HTTP-Requests gegen `/api/v1`. Keine
  direkte Engine-Nutzung, keine Python-Logik, keine Berechnung, keine Scores,
  keine Recommendation-Logik, keine Analyse auf dem Gerät.
- **Read-only / sicher:** keine Broker, keine Orders, keine Kauf-/Verkaufsknöpfe,
  keine Trading-Funktionen. Alle Kauf-/Verkaufsentscheidungen trifft der Benutzer.
- **Keine Änderungen am Backend:** Sprint 18 hat keine bestehende Engine oder die
  Application-Schicht verändert.

## Technologie

| Bereich | Wahl |
| --- | --- |
| Sprache | Kotlin |
| UI | Jetpack Compose, Material Design 3 |
| Architektur | MVVM + Repository Pattern |
| Zustand | `StateFlow`, Coroutines |
| Netzwerk | Retrofit + OkHttp + kotlinx.serialization |
| Lokaler Cache | Room (nur Offline-Cache) |
| Bilder | Coil |
| Navigation | Navigation Compose |
| DI | manueller `AppContainer` (kein Framework) |

Kein Flutter, keine WebView, keine Hybrid-App.

## Architektur (Schichten)

```
ui/ (Compose Screens + ViewModels, StateFlow)
        │  nutzt Repositories + Domänenmodelle
data/repository/ (OpportunityRepository, MarketRepository, SystemRepository, HistoryRepository)
        │  REST (data/remote) + Cache (data/local, Room) + Mapper
domain/model/ (reine Anzeige-Modelle, framework-frei)
```

- `ui` greift **nie** direkt auf `data.remote`/`data.local` zu (nur über
  Repositories/Domäne). `domain` ist frei von Android/Retrofit/Room. Diese Regeln
  werden von `ArchitectureTest` statisch geprüft (Architecture Check).
- Der Netzwerk-Host ist zur Laufzeit konfigurierbar
  (`HostSelectionInterceptor`), sodass die Backend-Adresse in den Einstellungen
  geändert werden kann.

## Bildschirme

- **Home (Start):** sofortiger Überblick – Marktstatus (Europa/USA, aktive
  Börsen, Countdown), letzter/nächster Scan, Top-Chancen, neue Chancen/Risiken,
  Systemstatus. Keine Wartebildschirme.
- **Opportunities:** Liste aller Chancen mit Suche, Richtungsfilter
  (Long/Short), Sortierung (Score/Confidence/Risk/Rang) sowie Markt/Branche.
- **Detailseite:** Ticker, Unternehmen, Summary, Reasons, Warnings, Direction,
  Strength, Opportunity Score, Confidence, Risk, Pattern, Strategien, Analytics,
  Backtest, Paper Trading, Market Intelligence, Zeitpunkt der Analyse.
- **Markets:** Europa/USA, aktive Session, Marktstatus, Discovery-Status.
- **History:** letzte Scans mit Zeitpunkt und Top-Chancen (lokal gespeichert).
- **Settings:** Backend-Adresse, Auto-Refresh, Dark Theme, Hintergrund-Refresh,
  Cache-Hinweis, Debug-Informationen.

## Auto-Refresh & Offline

- Aktualisierung beim Start, beim Resume und per Pull-to-Refresh; optionaler
  Hintergrund-Refresh. Doppelte gleichzeitige Aktualisierungen werden vermieden.
- **Offline:** ohne Verbindung zeigt die App den zuletzt erfolgreich gespeicherten
  Scan aus dem Room-Cache und weist den Zeitpunkt deutlich aus (Offline-Banner).

## Design

Dunkles „Carbon"-Theme mit gelber Akzentfarbe, große Karten, Material 3,
einhandbedienbar, dezente Animationen, aufgeräumt – konsistent zur Desktop-
Version.

## Tests & Qualität

- Unit-Tests: Serialisierung/Envelope, Mapper, Repositories (inkl. Offline/Cache),
  alle ViewModels, State-Management.
- UI-Tests: Chancen-Karte und Bottom-Navigation (Compose-UI-Tests).
- Architecture Check: `ArchitectureTest` erzwingt die Schichtung und verbietet
  Handels-Aktionen im Quellcode.
- Statische Analyse: **ktlint** und **detekt** (Konfiguration in `android/`).

## Bauen

Siehe [`INSTALLATION_ANDROID.md`](INSTALLATION_ANDROID.md). Kurz:

```bash
cd android
./gradlew assembleDebug testDebugUnitTest ktlintCheck detekt
```

> Hinweis: Der Bau benötigt das Android SDK (compileSdk 34) und JDK 17.
