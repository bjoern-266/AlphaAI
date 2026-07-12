package com.alphaai.app.ui.common

/**
 * Reine Anzeige-Formatierung (keine Fachlogik).
 *
 * Wandelt bereits vorhandene Werte in gut lesbare Zeichenketten um – es werden
 * keine Kennzahlen berechnet oder abgeleitet.
 */
object Format {
    /** Formatiert eine 0..100-Kennzahl als ganze Zahl, sonst „—". */
    fun score(value: Double?): String = value?.let { "${it.toInt()}" } ?: "—"

    /** Formatiert eine 0..1-Confidence als Prozent, sonst „—". */
    fun percent(value: Double?): String = value?.let { "${(it * PERCENT).toInt()} %" } ?: "—"

    /** Formatiert eine Risiko-Kennzahl (0..100), sonst „—". */
    fun risk(value: Double?): String = value?.let { "${it.toInt()}" } ?: "—"

    /** Formatiert einen Countdown in Sekunden als „H:MM:SS" bzw. „M:SS". */
    fun countdown(seconds: Int?): String {
        if (seconds == null || seconds < 0) return "—"
        val hours = seconds / SECONDS_PER_HOUR
        val minutes = (seconds % SECONDS_PER_HOUR) / SECONDS_PER_MINUTE
        val secs = seconds % SECONDS_PER_MINUTE
        return if (hours > 0) {
            "%d:%02d:%02d".format(hours, minutes, secs)
        } else {
            "%d:%02d".format(minutes, secs)
        }
    }

    /**
     * Kürzt einen ISO-8601-Zeitstempel auf „YYYY-MM-DD HH:MM" (reine Anzeige).
     *
     * Fällt bei unerwartetem Format auf den Rohwert zurück (keine Verfälschung).
     */
    fun timestamp(iso: String?): String {
        if (iso.isNullOrBlank()) return "—"
        val normalized = iso.replace('T', ' ')
        val cutoff = normalized.indexOf('.').let { if (it >= 0) it else normalized.length }
        val trimmed = normalized.substring(0, cutoff)
        return trimmed.take(MINUTE_LENGTH)
    }

    private const val PERCENT = 100
    private const val SECONDS_PER_MINUTE = 60
    private const val SECONDS_PER_HOUR = 3600
    private const val MINUTE_LENGTH = 16
}
