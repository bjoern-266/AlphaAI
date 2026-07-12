package com.alphaai.app

import com.alphaai.app.core.AppResult
import com.alphaai.app.data.repository.OpportunityRepository
import com.alphaai.app.fake.FakeAlphaAiApi
import com.alphaai.app.fake.FakeOpportunityDao
import com.alphaai.app.fake.Fixtures
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Tests des OpportunityRepository (API-Zugriff, Cache, Offline-Fallback). */
class OpportunityRepositoryTest {
    private val api = FakeAlphaAiApi()
    private val dao = FakeOpportunityDao()
    private val repository = OpportunityRepository(api, dao, now = { 1L })

    @Test
    fun `opportunities success returns list and caches`() =
        runTest {
            api.opportunitiesResponse =
                FakeAlphaAiApi.ok(
                    com.alphaai.app.data.remote.dto.OpportunityReportDto(
                        opportunities = listOf(Fixtures.opportunity("AAPL"), Fixtures.opportunity("MSFT", rank = 2)),
                    ),
                )

            val result = repository.opportunities()

            assertTrue(result is AppResult.Success)
            assertEquals(2, (result as AppResult.Success).data.size)
            assertEquals(2, dao.all().size)
        }

    @Test
    fun `opportunities offline returns cached data`() =
        runTest {
            // Zuerst erfolgreich cachen.
            api.opportunitiesResponse =
                FakeAlphaAiApi.ok(
                    com.alphaai.app.data.remote.dto.OpportunityReportDto(
                        opportunities = listOf(Fixtures.opportunity("AAPL")),
                    ),
                )
            repository.opportunities()

            // Dann Netzwerkfehler simulieren.
            api.failWith = FakeAlphaAiApi.offline()
            val result = repository.opportunities()

            assertTrue(result is AppResult.Offline)
            assertEquals("AAPL", (result as AppResult.Offline).data.single().ticker)
        }

    @Test
    fun `top offline without cache fails`() =
        runTest {
            api.failWith = FakeAlphaAiApi.offline()
            val result = repository.topOpportunities(10)
            assertTrue(result is AppResult.Offline || result is AppResult.Failure)
        }

    @Test
    fun `detail uses recommendation fallback when opportunity missing`() =
        runTest {
            api.opportunityResponse = FakeAlphaAiApi.failure()
            api.recommendationResponse = FakeAlphaAiApi.ok(Fixtures.opportunity("TSLA"))

            val result = repository.detail("TSLA")

            assertTrue(result is AppResult.Success)
            assertEquals("TSLA", (result as AppResult.Success).data.ticker)
        }

    @Test
    fun `detail offline falls back to cache`() =
        runTest {
            api.opportunityResponse = FakeAlphaAiApi.ok(Fixtures.opportunity("NVDA"))
            repository.detail("NVDA") // cache befüllen

            api.failWith = FakeAlphaAiApi.offline()
            val result = repository.detail("NVDA")

            assertTrue(result is AppResult.Offline)
            assertEquals("NVDA", (result as AppResult.Offline).data.ticker)
        }

    @Test
    fun `detail unknown ticker fails`() =
        runTest {
            api.opportunityResponse = FakeAlphaAiApi.failure()
            api.recommendationResponse = FakeAlphaAiApi.failure()
            val result = repository.detail("ZZZ")
            assertTrue(result is AppResult.Failure)
        }
}
