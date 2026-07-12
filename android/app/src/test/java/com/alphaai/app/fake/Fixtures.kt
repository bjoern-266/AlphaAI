package com.alphaai.app.fake

import com.alphaai.app.data.remote.dto.MarketClockDto
import com.alphaai.app.data.remote.dto.MarketStateDto
import com.alphaai.app.data.remote.dto.OperationReportDto
import com.alphaai.app.data.remote.dto.OpportunityDto
import com.alphaai.app.data.remote.dto.SystemStateDto
import com.alphaai.app.data.remote.dto.HeartbeatDto

/** Test-Beispieldaten (DTOs). */
object Fixtures {
    fun opportunity(
        ticker: String,
        score: Double = 80.0,
        direction: String = "long",
        rank: Int = 1,
        confidence: Double = 0.8,
        risk: Double = 70.0,
        market: String = "NASDAQ",
        sector: String = "Technology",
    ): OpportunityDto =
        OpportunityDto(
            ticker = ticker,
            company = "$ticker Inc.",
            market = market,
            sector = sector,
            direction = direction,
            recommendationStrength = "high",
            confidence = confidence,
            opportunityScore = score,
            risk = risk,
            opportunityRank = rank,
            summary = "Zusammenfassung $ticker",
            reasons = listOf("Grund A", "Grund B"),
            warnings = listOf("Warnung"),
            patternSummary = "Muster",
            strategySummary = "Strategie",
        )

    fun operations(
        session: String = "USA: open",
        lastScan: String = "2026-07-12T14:00:00+00:00",
        newOpportunities: List<String> = listOf("AAPL"),
    ): OperationReportDto =
        OperationReportDto(
            asOf = "2026-07-12T14:30:00+00:00",
            currentSession = session,
            marketClock =
                MarketClockDto(
                    markets =
                        listOf(
                            MarketStateDto("us", "USA", "open", isOpen = true, nextPhase = "close", secondsToNext = 3600),
                            MarketStateDto("europe", "Europa", "close", isOpen = false, nextPhase = "pre_market"),
                        ),
                    openMarkets = listOf("us"),
                    nextOpenMarket = "europe",
                ),
            lastScanAt = lastScan,
            nextScanAt = "2026-07-12T15:00:00+00:00",
            nextScanJob = "discovery_us",
            scanCount = 4,
            systemState =
                SystemStateDto(
                    health = "ok",
                    heartbeat = HeartbeatDto(alive = true, ageSeconds = 5),
                    scanCount = 4,
                    uptimeSeconds = 3600,
                ),
            newOpportunities = newOpportunities,
        )
}
