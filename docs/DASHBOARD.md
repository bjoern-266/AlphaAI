# Dashboard (AlphaAI Command Center)

_Wird laufend gepflegt._ Diese Datei beschreibt das Dashboard aus Sprint 13. Es
ist **ausschließlich** die Presentation Layer: es **berechnet niemals** Daten,
enthält **keinerlei** Geschäftslogik und erzeugt **keine** Scores, Risiken,
Empfehlungen, Analysen, Kennzahlen oder Statistiken. Es **zeigt** ausschließlich
bereits vorhandene Report-Werte an. Fehlt ein Wert, wird lediglich ein
Platzhalter angezeigt – **keine** Ersatzberechnung.

## Idee in einem Satz

Das Command Center macht die bereits vorhandenen Ergebnisse von AlphaAI sichtbar
– als hochwertiges, industrielles „Dark Carbon"-Cockpit – ohne selbst je eine
Zahl zu berechnen.

## Kette

```
Reports (Analytics / PaperTrading / Backtest / Recommendation / Risk /
         Score / Strategy / Pattern / Indicator)
        ↓  ReportBundle
DashboardEngine
        ↓  build_view_model()  (liest Reports ab, rechnet nichts)
DashboardViewModel
        ↓  Widgets (Registry) → WidgetSpec (reine Anzeige-Beschreibung)
        ↓  Router (Seiten-Layout) + Responsive (Geräteklasse)
DashboardView
        ↓  render.py / app.py  (die einzige Streamlit-Schicht)
Streamlit-UI
```

Die Engine **liest** ausschließlich; sie schreibt nichts zurück und ändert keine
Engine, kein Backtesting, kein Paper Trading und kein Analytics.

## Bausteine

Paket `dashboard/` (Subsystem, wie `pipeline/`/`analytics/` – nur der
Zyklenprüfung unterworfen):

| Modul | Aufgabe |
|---|---|
| `theme.py` | **Die einzige** Quelle des Aussehens: Dark-Carbon-Palette, Typografie, Abstände, Rahmen/Radien, Animationen, Icons, Materialien, Chart-Palette. Keine Hardcodes im übrigen Code. |
| `state.py` | `DashboardState` (aktive Seite, Tabs, Filter, Sortierung, Zoom, Sidebar, Suche, Refresh-Rate, Geräteklasse, Chart-Optionen). `snapshot()`/`restore()` sichern den Zustand vollständig – er geht nie verloren. |
| `format.py` | Reine Anzeige-Formatierung (Währung, Prozent, Zahlen, Vorzeichen, Platzhalter `—`). Rechnet nichts. |
| `charts.py` | Baut `ChartSpec`-Beschreibungen (Linie/Fläche/Balken/Donut) aus vorhandenen Werten. Farben ausschließlich aus der Theme-Chart-Palette. |
| `status.py` | Leitet den Modulstatus (online/no_data/offline/degraded) rein aus dem **Vorhandensein** der Reports ab. |
| `settings.py` + `settings.toml` | Lädt **nur** Anzeigeoptionen (Startseite, Dark Mode, Refresh-Optionen, Charttyp, Tabellenseiten, Export). **Keine** Handelsparameter. |
| `viewmodels.py` | `ReportBundle` (Eingabe) → `DashboardViewModel`. Liest die Report-Felder ab; fehlt ein Wert, bleibt er `None` (Platzhalter). Keine Berechnung. |
| `responsive.py` | Ordnet die Widget-Regionen je Geräteklasse um (Desktop/UltraWide/4K dreispaltig, Tablet einspaltig). Kein Smartphone-Ziel. |
| `feedback.py` | Baut Lade-/Fehler-Widgets (Skeleton/Progress/Fade bzw. offline/no_data/…). Keine Exceptions im Frontend. |
| `widgets/` | 26 unabhängige Widgets; jedes liest nur das View Model und liefert eine `WidgetSpec`. Kein Widget importiert ein anderes (gemeinsame Bausteine in `widgets/common.py`). |
| `widget_registry.py` | **Die einzige** Stelle, an der Widgets bekannt gemacht werden (Open/Closed). |
| `router.py` | Ordnet jeder der 9 Seiten ihre Widgets zu; Navigationseinträge und Tastenkürzel. Neue Seiten kommen **ausschließlich** hier hinzu. |
| `engine.py` | `DashboardEngine`: setzt aus View Model + Router + Registry eine `DashboardView` zusammen. Bleibt für neue Widgets/Seiten **unverändert**. |
| `render.py` / `app.py` | Die **einzige** Streamlit-Schicht (lazy Import, `# pragma: no cover`). Zeichnet nur die fertigen `WidgetSpec`s. |

## Seiten (9)

Overview · Live Analysis · Paper Portfolio · Backtesting · Analytics ·
Performance · Trade Journal · Recommendations · Settings.

Tastenkürzel: `F5` = Refresh, `Ctrl+1` Overview, `Ctrl+2` Analytics,
`Ctrl+3` Paper Portfolio, `Ctrl+4` Backtesting, `Ctrl+5` Trade Journal.

## Design „Dark Carbon"

Industriell, hochwertig, minimalistisch, futuristisch – die Atmosphäre eines
professionellen Trading-Intelligence-Command-Centers. Keine Logos, keine Namen,
keine geschützten Elemente. ~90 % Schwarz/Grau, ~10 % gelbe Akzente.

| Rolle | Farbe |
|---|---|
| Primary Background | `#090909` |
| Secondary Background | `#111111` |
| Carbon Surface | `#171717` |
| Cards | `#1F1F1F` |
| Borders | `#2E2E2E` |
| Carbon Highlight | `#343434` |
| Primary Accent | `#F2C94C` |
| Hover Accent | `#FFD54F` |
| Success | `#27AE60` |
| Warning | `#F2994A` |
| Danger | `#EB5757` |
| Information | `#56CCF2` |
| Text | `#F5F5F5` |
| Secondary Text | `#A8A8A8` |

Schriften: Inter (primär), JetBrains Mono (Zahlen/Mono), IBM Plex Sans
(Alternative). Chart-Farben ausschließlich Schwarz-Hintergrund + Gold/Grün/Rot/
Cyan/Grau.

## Zustände

- **Ladezustände:** Skeleton / Progress / Fade – nie eine leere Seite.
- **Fehlerzustände:** loading / offline / no_data / disconnected / timeout /
  error – als Anzeige, **niemals** als Exception im Frontend. Fehler eines
  einzelnen Widgets werden isoliert als Platzhalter dargestellt.
- **Responsive:** Desktop, Tablet, UltraWide, 4K (kein Smartphone).
- **Auto-Refresh:** 1/5/15/30/60 s + manuell; lädt **nur** neue Reports und
  startet **nie** eine Berechnung.

## Was das Dashboard bewusst NICHT tut

- Es berechnet nichts (keine Scores/Risiken/Empfehlungen/Analysen/Kennzahlen).
- Es enthält keine Handelsparameter und keine Geschäftslogik.
- Es verändert keine Reports und ruft keine Engine zur Berechnung auf.
- Es hat keine Broker-API und löst keine Orders aus.

## Erweitern

- **Neues Widget:** Klasse von `BaseWidget` ableiten, in `widget_registry.py`
  registrieren, im `router.py` einer Seite/Region zuordnen. Die Engine bleibt
  unverändert.
- **Neue Seite:** `Page`-Wert + Layout im `router.py` ergänzen. Die Engine
  bleibt unverändert.
- **Aussehen ändern:** ausschließlich in `theme.py`.

## Tests

259 Tests decken Modelle, Theme, State (Snapshot/Restore), Format, Charts,
Status, Settings, View Models, alle Widgets, Registry, Router, Responsive,
Feedback und die Engine ab (inkl. Lade-/Fehler-/Widget-Isolationsfälle). Die
gesamte Dashboard-Logik ist Streamlit-frei und ohne installiertes Streamlit
testbar.
