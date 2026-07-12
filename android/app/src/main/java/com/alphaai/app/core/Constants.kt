package com.alphaai.app.core

/** Projektweite Konstanten (keine Fachlogik, nur technische Vorgaben). */
object Constants {
    /** Gemeinsames Präfix aller REST-Endpunkte (Versionierung). */
    const val API_PREFIX = "api/v1"

    /** Standardanzahl der auf der Startseite gezeigten Top-Chancen. */
    const val HOME_TOP_LIMIT = 10

    /** Netzwerk-Timeout in Sekunden. */
    const val NETWORK_TIMEOUT_SECONDS = 15L

    /** Standard-Aktualisierungsintervall des optionalen Hintergrund-Refresh (Minuten). */
    const val DEFAULT_REFRESH_MINUTES = 5
}
