package com.alphaai.app.domain.model

/** Handelsrichtung einer Chance (nur Anzeige – keine Order). */
enum class Direction(val label: String) {
    LONG("Long"),
    SHORT("Short"),
    NEUTRAL("Watch"),
    ;

    companion object {
        /** Bildet den serialisierten Backend-Wert auf die Enumeration ab. */
        fun fromApi(value: String?): Direction =
            when (value?.lowercase()) {
                "long" -> LONG
                "short" -> SHORT
                else -> NEUTRAL
            }
    }
}

/** Stärke/Qualität einer Empfehlung (unverändert aus dem Backend übernommen). */
enum class Strength(val label: String) {
    VERY_HIGH("Sehr hoch"),
    HIGH("Hoch"),
    MEDIUM("Mittel"),
    LOW("Niedrig"),
    REJECT("Verworfen"),
    UNKNOWN("—"),
    ;

    companion object {
        /** Bildet den serialisierten Backend-Wert auf die Enumeration ab. */
        fun fromApi(value: String?): Strength =
            when (value?.lowercase()) {
                "very_high" -> VERY_HIGH
                "high" -> HIGH
                "medium" -> MEDIUM
                "low" -> LOW
                "reject" -> REJECT
                else -> UNKNOWN
            }
    }
}

/** Gesundheitszustand einer Komponente oder des Gesamtsystems. */
enum class HealthLevel(val label: String) {
    OK("OK"),
    DEGRADED("Eingeschränkt"),
    ERROR("Fehler"),
    UNKNOWN("Unbekannt"),
    ;

    companion object {
        /** Bildet den serialisierten Backend-Wert auf die Enumeration ab. */
        fun fromApi(value: String?): HealthLevel =
            when (value?.lowercase()) {
                "ok" -> OK
                "degraded" -> DEGRADED
                "error" -> ERROR
                else -> UNKNOWN
            }
    }
}
