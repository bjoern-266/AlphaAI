package com.alphaai.app.data.remote

import com.alphaai.app.data.remote.dto.DiscoveryReportDto
import com.alphaai.app.data.remote.dto.EnvelopeDto
import com.alphaai.app.data.remote.dto.HealthDto
import com.alphaai.app.data.remote.dto.MarketStatusDto
import com.alphaai.app.data.remote.dto.OperationReportDto
import com.alphaai.app.data.remote.dto.OpportunityDto
import com.alphaai.app.data.remote.dto.OpportunityReportDto
import com.alphaai.app.data.remote.dto.ServiceInfoDto
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

/**
 * Retrofit-Beschreibung der AlphaAI REST-API (`/api/v1`).
 *
 * Die App **konsumiert** ausschließlich diese Endpunkte. Sie enthält keine
 * Geschäftslogik: alle Werte stammen unverändert aus den Backend-Reports. Jeder
 * Endpunkt liefert die einheitliche [EnvelopeDto]-Hülle.
 */
interface AlphaAiApi {
    @GET("api/v1/version")
    suspend fun version(): EnvelopeDto<ServiceInfoDto>

    @GET("api/v1/health")
    suspend fun health(): EnvelopeDto<HealthDto>

    @GET("api/v1/operations")
    suspend fun operations(): EnvelopeDto<OperationReportDto>

    @GET("api/v1/market-status")
    suspend fun marketStatus(): EnvelopeDto<MarketStatusDto>

    @GET("api/v1/opportunities")
    suspend fun opportunities(): EnvelopeDto<OpportunityReportDto>

    @GET("api/v1/opportunities/top")
    suspend fun topOpportunities(
        @Query("limit") limit: Int,
    ): EnvelopeDto<List<OpportunityDto>>

    @GET("api/v1/opportunities/{ticker}")
    suspend fun opportunity(
        @Path("ticker") ticker: String,
    ): EnvelopeDto<OpportunityDto>

    @GET("api/v1/discovery")
    suspend fun discovery(): EnvelopeDto<DiscoveryReportDto>

    @GET("api/v1/recommendations/{ticker}")
    suspend fun recommendation(
        @Path("ticker") ticker: String,
    ): EnvelopeDto<OpportunityDto>
}
