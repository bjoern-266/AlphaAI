# AlphaAI Android App

Native Android-Client (Kotlin, Jetpack Compose, Material 3) für das AlphaAI
Backend. Die App ist ein **reiner REST-Client**: sie konsumiert ausschließlich
die REST-API (`/api/v1`) und enthält **keine** Analyse, **keine** Berechnung und
**keine** Handelsfunktionen (Read-only, keine Broker/Orders).

## Bauen

```bash
cd android
./gradlew assembleDebug        # Debug-APK bauen
./gradlew testDebugUnitTest    # Unit-Tests
./gradlew ktlintCheck detekt   # Statische Analyse
./gradlew connectedAndroidTest # UI-Tests (Emulator/Gerät nötig)
```

Voraussetzungen: Android SDK (compileSdk 34), JDK 17. Die Backend-Adresse wird
in den App-Einstellungen gesetzt (Standard: `http://10.0.2.2:8000/` – der
Host-Rechner aus dem Emulator).

Details: [`../docs/ANDROID.md`](../docs/ANDROID.md),
[`../docs/USER_GUIDE.md`](../docs/USER_GUIDE.md),
[`../docs/INSTALLATION_ANDROID.md`](../docs/INSTALLATION_ANDROID.md).
