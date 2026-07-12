package com.alphaai.app.ui.theme

import androidx.compose.ui.graphics.Color

/**
 * Farbpalette des „Dark Carbon"-Themes mit gelber Akzentfarbe.
 *
 * Das Farbschema ist bewusst identisch zur Desktop-Version (dunkler
 * Carbon-Hintergrund, große Karten, gelbe Akzente für Aktionen/Hervorhebungen).
 */
internal object AlphaColors {
    val Carbon = Color(0xFF0E0F12)
    val CarbonElevated = Color(0xFF16181D)
    val CarbonCard = Color(0xFF1C1F26)
    val CarbonBorder = Color(0xFF2A2E37)

    val Amber = Color(0xFFFFC400)
    val AmberDim = Color(0xFFB98F00)
    val OnAmber = Color(0xFF1A1400)

    val TextPrimary = Color(0xFFF2F3F5)
    val TextSecondary = Color(0xFFA6ADBB)
    val TextMuted = Color(0xFF6B7280)

    val Long = Color(0xFF35D07F)
    val Short = Color(0xFFFF5C5C)
    val Neutral = Color(0xFF8A94A6)
    val Warning = Color(0xFFFFB020)

    val HealthOk = Color(0xFF35D07F)
    val HealthDegraded = Color(0xFFFFB020)
    val HealthError = Color(0xFFFF5C5C)
    val HealthUnknown = Color(0xFF6B7280)
}
