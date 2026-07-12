# Installation & Build – AlphaAI Android App

Diese Anleitung beschreibt, wie die Android-App gebaut und installiert wird. Die
App ist ein reiner REST-Client des AlphaAI-Backends.

## Voraussetzungen

- **JDK 17**
- **Android SDK** mit `compileSdk 34` (Android 14), Build-Tools passend zu AGP 8.5
- Optional: Android Studio (Koala oder neuer) – enthält SDK und Emulator
- Ein laufendes AlphaAI-Backend (siehe `docs/PRODUCTION.md`)

Das Projekt liegt im Verzeichnis `android/`. Es verwendet den Gradle-Wrapper
(`./gradlew`), einen zentralen Versionskatalog (`gradle/libs.versions.toml`) und
Kotlin 2.0.

## Projekt öffnen

- **Android Studio:** „Open" → Ordner `android/` wählen. Gradle synchronisiert
  automatisch.
- **Kommandozeile:** in das Verzeichnis `android/` wechseln.

Lege bei Bedarf `android/local.properties` mit dem SDK-Pfad an:

```properties
sdk.dir=/pfad/zum/Android/sdk
```

## Bauen

```bash
cd android

# Debug-APK erzeugen (Ausgabe unter app/build/outputs/apk/debug/)
./gradlew assembleDebug

# Unit-Tests (JVM)
./gradlew testDebugUnitTest

# Statische Analyse
./gradlew ktlintCheck detekt

# UI-/Instrumentierungstests (Emulator oder Gerät erforderlich)
./gradlew connectedAndroidTest
```

## Installieren

```bash
# Auf ein verbundenes Gerät/Emulator installieren
./gradlew installDebug
# oder die APK direkt aufspielen
adb install app/build/outputs/apk/debug/app-debug.apk
```

## Backend-Adresse einstellen

Nach dem Start: **Einstellungen → Backend-Adresse**.

- **Emulator:** `http://10.0.2.2:8000/` (der Host-Rechner aus Sicht des Emulators).
- **Physisches Gerät im selben WLAN:** `http://<IP-des-Backend-Rechners>:8000/`.

Standardmäßig erlaubt die App Klartext-HTTP nur für lokale Adressen
(`10.0.2.2`, `127.0.0.1`, `localhost`, lokale Netze). Für den lokalen Betrieb ist
keine weitere Konfiguration nötig; die Backend-Zugriffskontrolle ist derzeit auf
lokalen Zugriff beschränkt.

## Release-Build (optional)

```bash
./gradlew assembleRelease
```

Für einen signierten Release-Build ist eine Signaturkonfiguration erforderlich
(Keystore); der Release-Typ ist mit R8/ProGuard-Regeln (`app/proguard-rules.pro`)
vorbereitet.

## Fehlerbehebung

- **„SDK location not found"** → `local.properties` mit `sdk.dir` anlegen oder
  `ANDROID_HOME` setzen.
- **Keine Daten in der App** → prüfen, ob das Backend läuft und die
  Backend-Adresse korrekt gesetzt ist (`/api/v1/version` sollte antworten).
- **Offline-Banner** → es besteht keine Verbindung; die App zeigt den letzten
  gespeicherten Scan.
