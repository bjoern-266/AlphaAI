# AlphaAI – Schnellstart (Nutzung)

So bringst du AlphaAI zum Laufen. Zwei Teile: **1) Backend‑Dienst** (die
Analyse‑/API‑Zentrale) und **2) die Android‑App** (die Oberfläche). Die App
zeigt nur an – **alle Kauf-/Verkaufsentscheidungen triffst du selbst**.

---

## 1) Backend‑Dienst starten (REST‑API)

Voraussetzung: Python 3.12.

```bash
cd AlphaAI
pip install -e .            # installiert auch fastapi + uvicorn
python -m scripts.serve --demo
```

Das war’s. Der Dienst läuft dann auf `http://127.0.0.1:8000`.

- `--demo` lädt Beispiel‑Chancen, damit sofort etwas sichtbar ist (ohne echte
  Marktdaten). Für den echten Betrieb ohne `--demo` starten – dann liefert die
  API Daten, sobald echte Reports vorliegen.
- Im Browser ausprobieren:
  - `http://127.0.0.1:8000/docs` – interaktive API‑Übersicht (Swagger)
  - `http://127.0.0.1:8000/api/v1/opportunities/top?limit=5`
  - `http://127.0.0.1:8000/api/v1/health`
- Auf der Kommandozeile:
  ```bash
  curl http://127.0.0.1:8000/api/v1/opportunities/top?limit=5
  ```

### Fürs Handy erreichbar machen

```bash
python -m scripts.serve --demo --host 0.0.0.0 --port 8000
```

Und in `knowledge/application_rules.toml` unter `[api]` `auth_policy = "open"`
setzen (Standard ist „nur lokaler Zugriff"). Die Backend‑Adresse für die App ist
dann `http://<IP-deines-Rechners>:8000/`.

---

## 2) Android‑App bauen & installieren

> Die APK muss auf **deinem** Rechner gebaut werden – dafür wird das Android‑SDK
> gebraucht (in der Cloud‑Umgebung nicht verfügbar). Am einfachsten mit
> **Android Studio**, das SDK und Gradle mitbringt.

**Mit Android Studio (empfohlen):**
1. Android Studio öffnen → *Open* → Ordner `AlphaAI/android/` wählen.
2. Gradle synchronisiert automatisch (lädt AndroidX/Compose‑Abhängigkeiten).
3. Oben ein Gerät/Emulator wählen → ▶ *Run 'app'*.

**Auf der Kommandozeile** (Android‑SDK installiert, `local.properties` mit
`sdk.dir=...`):
```bash
cd AlphaAI/android
./gradlew assembleDebug        # baut app/build/outputs/apk/debug/app-debug.apk
./gradlew installDebug         # auf verbundenes Gerät/Emulator installieren
```

**Backend‑Adresse eintragen:** App öffnen → *Einstellungen* → *Backend‑Adresse*:
- Emulator: `http://10.0.2.2:8000/`
- echtes Handy im WLAN: `http://<IP-des-Rechners>:8000/`

Danach zeigt die Startseite Marktstatus, Countdown und Top‑Chancen.

---

## Ohne App nur schnell testen

Wenn du gar nichts installieren willst, siehst du die API‑Antworten direkt im
Browser über `http://127.0.0.1:8000/docs` (nach Schritt 1).

Mehr Details: `docs/PRODUCTION.md` (Backend), `docs/ANDROID.md`,
`docs/USER_GUIDE.md`, `docs/INSTALLATION_ANDROID.md` (App).
