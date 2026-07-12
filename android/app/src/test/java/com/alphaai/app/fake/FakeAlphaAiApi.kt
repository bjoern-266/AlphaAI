package com.alphaai.app.fake

import com.alphaai.app.data.remote.AlphaAiApi
import com.alphaai.app.data.remote.dto.DiscoveryReportDto
import com.alphaai.app.data.remote.dto.EnvelopeDto
import com.alphaai.app.data.remote.dto.HealthDto
import com.alphaai.app.data.remote.dto.MarketStatusDto
import com.alphaai.app.data.remote.dto.OperationReportDto
import com.alphaai.app.data.remote.dto.OpportunityDto
import com.alphaai.app.data.remote.dto.OpportunityReportDto
import com.alphaai.app.data.remote.dto.ServiceInfoDto
import java.io.IOException

/** Konfigurierbarer Test-Ersatz der REST-API (keine echten Netzwerkaufrufe). */
class FakeAlphaAiApi : AlphaAiApi {
    /** Wenn gesetzt, wirft jeder Aufruf diese Ausnahme (Netzwerk-/Offline-Test). */
    var failWith: Throwable? = null

    var versionResponse: EnvelopeDto<ServiceInfoDto> = ok(ServiceInfoDto(name = "AlphaAI"))
    var healthResponse: EnvelopeDto<HealthDto> = ok(HealthDto(status = "ok"))
    var operationsResponse: EnvelopeDto<OperationReportDto> = ok(OperationReportDto())
    var marketStatusResponse: EnvelopeDto<MarketStatusDto> = ok(MarketStatusDto())
    var opportunitiesResponse: EnvelopeDto<OpportunityReportDto> = ok(OpportunityReportDto())
    var topResponse: EnvelopeDto<List<OpportunityDto>> = ok(emptyList())
    var opportunityResponse: EnvelopeDto<OpportunityDto> = failure()
    var recommendationResponse: EnvelopeDto<OpportunityDto> = failure()
    var discoveryResponse: EnvelopeDto<DiscoveryReportDto> = ok(DiscoveryReportDto())

    var callCount = 0
        private set

    override suspend fun version() = guarded { versionResponse }

    override suspend fun health() = guarded { healthResponse }

    override suspend fun operations() = guarded { operationsResponse }

    override suspend fun marketStatus() = guarded { marketStatusResponse }

    override suspend fun opportunities() = guarded { opportunitiesResponse }

    override suspend fun topOpportunities(limit: Int) = guarded { topResponse }

    override suspend fun opportunity(ticker: String) = guarded { opportunityResponse }

    override suspend fun discovery() = guarded { discoveryResponse }

    override suspend fun recommendation(ticker: String) = guarded { recommendationResponse }

    private inline fun <T> guarded(block: () -> T): T {
        callCount++
        failWith?.let { throw it }
        return block()
    }

    companion object {
        fun <T> ok(data: T): EnvelopeDto<T> = EnvelopeDto(ok = true, data = data)

        fun <T> failure(): EnvelopeDto<T> = EnvelopeDto(ok = false, data = null)

        fun offline(): IOException = IOException("Keine Verbindung")
    }
}
