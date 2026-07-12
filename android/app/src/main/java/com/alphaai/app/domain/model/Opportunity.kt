package com.alphaai.app.domain.model

/**
 * Eine Chance (Opportunity) in der Anzeige-Repräsentation der App.
 *
 * Alle Werte stammen unverändert aus dem Backend-Report. Die App **berechnet
 * nichts**: keine Scores, keine Confidence, kein Risk, keine Empfehlung.
 */
data class Opportunity(
    val ticker: String,
    val company: String,
    val market: String,
    val sector: String,
    val direction: Direction,
    val strength: Strength,
    val confidence: Double?,
    val opportunityScore: Double?,
    val risk: Double?,
    val rank: Int,
    val summary: String,
    val reasons: List<String> = emptyList(),
    val warnings: List<String> = emptyList(),
    val patternSummary: String = "",
    val strategySummary: String = "",
    val analyticsSummary: String = "",
    val backtestSummary: String = "",
    val paperTradingSummary: String = "",
    val marketIntelligenceSummary: String = "",
    val analyzedAt: String? = null,
) {
    /** Ob die Chance long-gerichtet ist (nur Anzeige). */
    val isLong: Boolean get() = direction == Direction.LONG

    /** Ob die Chance short-gerichtet ist (nur Anzeige). */
    val isShort: Boolean get() = direction == Direction.SHORT
}
