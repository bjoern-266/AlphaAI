package com.alphaai.app.data.mapper

import com.alphaai.app.data.local.OpportunityEntity
import com.alphaai.app.data.local.SnapshotEntity
import com.alphaai.app.data.remote.dto.HealthDto
import com.alphaai.app.data.remote.dto.MarketStatusDto
import com.alphaai.app.data.remote.dto.OperationReportDto
import com.alphaai.app.data.remote.dto.OpportunityDto
import com.alphaai.app.data.remote.dto.ServiceInfoDto
import com.alphaai.app.domain.model.ComponentHealth
import com.alphaai.app.domain.model.Direction
import com.alphaai.app.domain.model.HealthLevel
import com.alphaai.app.domain.model.HealthReport
import com.alphaai.app.domain.model.MarketClock
import com.alphaai.app.domain.model.MarketState
import com.alphaai.app.domain.model.OperationSnapshot
import com.alphaai.app.domain.model.Opportunity
import com.alphaai.app.domain.model.ServiceInfo
import com.alphaai.app.domain.model.Strength

/**
 * Reine Umwandlungsfunktionen zwischen DTO, Domänenmodell und Cache-Entity.
 *
 * Es findet **keine** Berechnung oder Ableitung statt – nur strukturelle
 * Übernahme der bereits vorhandenen Werte.
 */

fun OpportunityDto.toDomain(): Opportunity =
    Opportunity(
        ticker = ticker,
        company = company,
        market = market,
        sector = sector,
        direction = Direction.fromApi(direction),
        strength = Strength.fromApi(recommendationStrength),
        confidence = confidence,
        opportunityScore = opportunityScore,
        risk = risk,
        rank = if (opportunityRank > 0) opportunityRank else rank,
        summary = summary,
        reasons = reasons,
        warnings = warnings,
        patternSummary = patternSummary,
        strategySummary = strategySummary,
        analyticsSummary = analyticsSummary,
        backtestSummary = backtestSummary,
        paperTradingSummary = paperTradingSummary,
        marketIntelligenceSummary = summary,
        analyzedAt = timestamp,
    )

fun Opportunity.toEntity(now: Long): OpportunityEntity =
    OpportunityEntity(
        ticker = ticker,
        company = company,
        market = market,
        sector = sector,
        direction = direction.name,
        strength = strength.name,
        confidence = confidence,
        opportunityScore = opportunityScore,
        risk = risk,
        rank = rank,
        summary = summary,
        reasons = reasons,
        warnings = warnings,
        patternSummary = patternSummary,
        strategySummary = strategySummary,
        analyticsSummary = analyticsSummary,
        backtestSummary = backtestSummary,
        paperTradingSummary = paperTradingSummary,
        analyzedAt = analyzedAt,
        cachedAt = now,
    )

fun OpportunityEntity.toDomain(): Opportunity =
    Opportunity(
        ticker = ticker,
        company = company,
        market = market,
        sector = sector,
        direction = runCatching { Direction.valueOf(direction) }.getOrDefault(Direction.NEUTRAL),
        strength = runCatching { Strength.valueOf(strength) }.getOrDefault(Strength.UNKNOWN),
        confidence = confidence,
        opportunityScore = opportunityScore,
        risk = risk,
        rank = rank,
        summary = summary,
        reasons = reasons,
        warnings = warnings,
        patternSummary = patternSummary,
        strategySummary = strategySummary,
        analyticsSummary = analyticsSummary,
        backtestSummary = backtestSummary,
        paperTradingSummary = paperTradingSummary,
        marketIntelligenceSummary = summary,
        analyzedAt = analyzedAt,
    )

fun OperationReportDto.toSnapshot(): OperationSnapshot {
    val clock = marketClock
    val state = systemState
    return OperationSnapshot(
        asOf = asOf,
        currentSession = currentSession,
        markets = clock?.markets?.map { it.toDomain() } ?: emptyList(),
        openMarkets = clock?.openMarkets ?: emptyList(),
        nextOpenMarket = clock?.nextOpenMarket ?: "",
        nextOpenAt = clock?.nextOpenAt,
        lastScanAt = lastScanAt,
        nextScanAt = nextScanAt,
        nextScanJob = nextScanJob,
        runningJob = runningJob,
        scanCount = scanCount,
        errorCount = errorCount,
        health = HealthLevel.fromApi(state?.health),
        heartbeatAlive = state?.heartbeat?.alive ?: false,
        newOpportunities = newOpportunities,
        newRisks = newRisks,
    )
}

fun com.alphaai.app.data.remote.dto.MarketStateDto.toDomain(): MarketState =
    MarketState(
        key = key,
        title = title,
        phase = phase,
        isOpen = isOpen,
        nextPhase = nextPhase,
        secondsToNext = secondsToNext,
    )

fun MarketStatusDto.toDomain(): MarketClock =
    MarketClock(
        asOf = asOf,
        currentSession = currentSession,
        markets = markets.map { it.toDomain() },
        openMarkets = openMarkets,
        nextOpenMarket = nextOpenMarket,
        nextOpenAt = nextOpenAt,
    )

fun HealthDto.toDomain(): HealthReport =
    HealthReport(
        level = HealthLevel.fromApi(status),
        components =
            components.map {
                ComponentHealth(it.name, HealthLevel.fromApi(it.status), it.detail)
            },
        uptimeSeconds = uptimeSeconds,
        version = version,
        asOf = asOf,
    )

fun ServiceInfoDto.toDomain(): ServiceInfo =
    ServiceInfo(
        name = name,
        version = version,
        apiVersion = apiVersion,
        environment = environment,
        uptimeSeconds = uptimeSeconds,
    )

fun OperationSnapshot.toEntity(now: Long): SnapshotEntity =
    SnapshotEntity(
        id = 0,
        asOf = asOf,
        currentSession = currentSession,
        marketsJson = markets.joinToString("|") { "${it.key};${it.title};${it.phase};${it.isOpen}" },
        openMarkets = openMarkets,
        nextOpenMarket = nextOpenMarket,
        nextOpenAt = nextOpenAt,
        lastScanAt = lastScanAt,
        nextScanAt = nextScanAt,
        nextScanJob = nextScanJob,
        runningJob = runningJob,
        scanCount = scanCount,
        errorCount = errorCount,
        health = health.name,
        heartbeatAlive = heartbeatAlive,
        newOpportunities = newOpportunities,
        newRisks = newRisks,
        cachedAt = now,
    )

fun SnapshotEntity.toDomain(): OperationSnapshot =
    OperationSnapshot(
        asOf = asOf,
        currentSession = currentSession,
        markets = parseMarkets(marketsJson),
        openMarkets = openMarkets,
        nextOpenMarket = nextOpenMarket,
        nextOpenAt = nextOpenAt,
        lastScanAt = lastScanAt,
        nextScanAt = nextScanAt,
        nextScanJob = nextScanJob,
        runningJob = runningJob,
        scanCount = scanCount,
        errorCount = errorCount,
        health = runCatching { HealthLevel.valueOf(health) }.getOrDefault(HealthLevel.UNKNOWN),
        heartbeatAlive = heartbeatAlive,
        newOpportunities = newOpportunities,
        newRisks = newRisks,
    )

private fun parseMarkets(raw: String): List<MarketState> =
    if (raw.isBlank()) {
        emptyList()
    } else {
        raw.split("|").mapNotNull { part ->
            val fields = part.split(";")
            if (fields.size >= 4) {
                MarketState(
                    key = fields[0],
                    title = fields[1],
                    phase = fields[2],
                    isOpen = fields[3].toBooleanStrictOrNull() ?: false,
                    nextPhase = "",
                    secondsToNext = null,
                )
            } else {
                null
            }
        }
    }
