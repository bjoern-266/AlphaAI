package com.alphaai.app.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Operations-Report der Live Operations Platform (Backend). */
@Serializable
data class OperationReportDto(
    @SerialName("as_of") val asOf: String? = null,
    @SerialName("current_session") val currentSession: String = "",
    @SerialName("market_clock") val marketClock: MarketClockDto? = null,
    @SerialName("last_successful_scan_at") val lastScanAt: String? = null,
    @SerialName("next_scan_at") val nextScanAt: String? = null,
    @SerialName("next_scan_job") val nextScanJob: String = "",
    @SerialName("running_job") val runningJob: String? = null,
    @SerialName("scan_count") val scanCount: Int = 0,
    @SerialName("error_count") val errorCount: Int = 0,
    @SerialName("system_state") val systemState: SystemStateDto? = null,
    @SerialName("new_opportunities") val newOpportunities: List<String> = emptyList(),
    @SerialName("new_risks") val newRisks: List<String> = emptyList(),
    @SerialName("job_history") val jobHistory: List<JobRunDto> = emptyList(),
)

/** Zustand aller Märkte (Marktuhr). */
@Serializable
data class MarketClockDto(
    @SerialName("as_of") val asOf: String? = null,
    val markets: List<MarketStateDto> = emptyList(),
    @SerialName("open_markets") val openMarkets: List<String> = emptyList(),
    @SerialName("next_open_market") val nextOpenMarket: String = "",
    @SerialName("next_open_at") val nextOpenAt: String? = null,
)

/** Zusammengefasste Marktuhr (`/market-status`). */
@Serializable
data class MarketStatusDto(
    @SerialName("as_of") val asOf: String? = null,
    @SerialName("current_session") val currentSession: String = "",
    @SerialName("open_markets") val openMarkets: List<String> = emptyList(),
    @SerialName("next_open_market") val nextOpenMarket: String = "",
    @SerialName("next_open_at") val nextOpenAt: String? = null,
    val markets: List<MarketStateDto> = emptyList(),
)

/** Zustand eines einzelnen Marktes. */
@Serializable
data class MarketStateDto(
    val key: String = "",
    val title: String = "",
    val phase: String = "",
    @SerialName("is_open") val isOpen: Boolean = false,
    @SerialName("next_phase") val nextPhase: String = "",
    @SerialName("seconds_to_next") val secondsToNext: Int? = null,
)

/** Systemzustand (Health/Heartbeat/Queue …). */
@Serializable
data class SystemStateDto(
    val health: String = "unknown",
    val heartbeat: HeartbeatDto? = null,
    @SerialName("queue_size") val queueSize: Int = 0,
    @SerialName("scan_count") val scanCount: Int = 0,
    @SerialName("error_count") val errorCount: Int = 0,
    @SerialName("uptime_seconds") val uptimeSeconds: Int? = null,
)

/** Heartbeat des Hintergrunddienstes. */
@Serializable
data class HeartbeatDto(
    val alive: Boolean = false,
    @SerialName("age_seconds") val ageSeconds: Int? = null,
)

/** Ein Job-Lauf der Historie. */
@Serializable
data class JobRunDto(
    val name: String = "",
    @SerialName("job_type") val jobType: String = "",
    val status: String = "",
    @SerialName("duration_seconds") val durationSeconds: Double? = null,
    val error: String = "",
    val summary: String = "",
)
