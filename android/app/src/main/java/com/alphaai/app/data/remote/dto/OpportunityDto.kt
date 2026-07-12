package com.alphaai.app.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * Eine Chance, wie sie das Backend serialisiert.
 *
 * Deckt sowohl den Opportunity-Report (`opportunity_rank`) als auch den
 * Discovery-Report (`rank`) ab – beide Rang-Felder sind optional.
 */
@Serializable
data class OpportunityDto(
    val ticker: String = "",
    val company: String = "",
    val market: String = "",
    val sector: String = "",
    val country: String = "",
    val direction: String = "neutral",
    @SerialName("recommendation_strength") val recommendationStrength: String = "unknown",
    val confidence: Double? = null,
    @SerialName("opportunity_score") val opportunityScore: Double? = null,
    val risk: Double? = null,
    @SerialName("opportunity_rank") val opportunityRank: Int = 0,
    val rank: Int = 0,
    val summary: String = "",
    val reasons: List<String> = emptyList(),
    val warnings: List<String> = emptyList(),
    @SerialName("pattern_summary") val patternSummary: String = "",
    @SerialName("strategy_summary") val strategySummary: String = "",
    @SerialName("analytics_summary") val analyticsSummary: String = "",
    @SerialName("backtest_summary") val backtestSummary: String = "",
    @SerialName("paper_trading_summary") val paperTradingSummary: String = "",
    val timestamp: String? = null,
)

/** Opportunity-Report (Market Intelligence). */
@Serializable
data class OpportunityReportDto(
    val opportunities: List<OpportunityDto> = emptyList(),
    val statistics: OpportunityStatisticsDto? = null,
)

/** Discovery-Report (Market Discovery). */
@Serializable
data class DiscoveryReportDto(
    val opportunities: List<OpportunityDto> = emptyList(),
    val statistics: DiscoveryStatisticsDto? = null,
    val markets: List<String> = emptyList(),
)

/** Aggregierte Kennzahlen des Opportunity-Reports. */
@Serializable
data class OpportunityStatisticsDto(
    @SerialName("analyzed_count") val analyzedCount: Int? = null,
    @SerialName("long_count") val longCount: Int? = null,
    @SerialName("short_count") val shortCount: Int? = null,
    @SerialName("average_score") val averageScore: Double? = null,
    @SerialName("average_risk") val averageRisk: Double? = null,
)

/** Aggregierte Kennzahlen des Discovery-Reports. */
@Serializable
data class DiscoveryStatisticsDto(
    @SerialName("universe_count") val universeCount: Int? = null,
    @SerialName("rejected_count") val rejectedCount: Int? = null,
    @SerialName("analyzed_count") val analyzedCount: Int? = null,
)
