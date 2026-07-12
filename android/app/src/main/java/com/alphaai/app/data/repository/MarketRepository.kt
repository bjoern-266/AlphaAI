package com.alphaai.app.data.repository

import com.alphaai.app.core.AppResult
import com.alphaai.app.data.mapper.toDomain
import com.alphaai.app.data.remote.AlphaAiApi
import com.alphaai.app.domain.model.DiscoveryStatus
import com.alphaai.app.domain.model.MarketClock

/** Liest Markt- und Discovery-Zustände aus der REST-API (keine Berechnung). */
class MarketRepository(
    private val api: AlphaAiApi,
) {
    /** Lädt die zusammengefasste Marktuhr (`/market-status`). */
    suspend fun marketStatus(): AppResult<MarketClock> =
        fetch(remote = { api.marketStatus() }, map = { it.toDomain() })

    /** Lädt den Discovery-Zustand (`/discovery`). */
    suspend fun discovery(): AppResult<DiscoveryStatus> =
        fetch(
            remote = { api.discovery() },
            map = { report ->
                DiscoveryStatus(
                    universeCount = report.statistics?.universeCount,
                    analyzedCount = report.statistics?.analyzedCount,
                    rejectedCount = report.statistics?.rejectedCount,
                    opportunityCount = report.opportunities.size,
                    markets = report.markets,
                )
            },
        )
}
