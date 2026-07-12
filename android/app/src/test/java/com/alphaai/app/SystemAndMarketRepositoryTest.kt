package com.alphaai.app

import com.alphaai.app.core.AppResult
import com.alphaai.app.data.remote.dto.DiscoveryReportDto
import com.alphaai.app.data.remote.dto.DiscoveryStatisticsDto
import com.alphaai.app.data.repository.HistoryRepository
import com.alphaai.app.data.repository.MarketRepository
import com.alphaai.app.data.repository.SystemRepository
import com.alphaai.app.fake.FakeAlphaAiApi
import com.alphaai.app.fake.FakeScanHistoryDao
import com.alphaai.app.fake.FakeSnapshotDao
import com.alphaai.app.fake.Fixtures
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Tests der System-, Markt- und History-Repositories. */
class SystemAndMarketRepositoryTest {
    private val api = FakeAlphaAiApi()
    private val snapshotDao = FakeSnapshotDao()
    private val historyDao = FakeScanHistoryDao()

    private fun systemRepo() =
        SystemRepository(
            api = api,
            snapshotDao = snapshotDao,
            historyDao = historyDao,
            topTickersProvider = { listOf("AAPL", "MSFT") },
            now = { 1L },
        )

    @Test
    fun `snapshot success caches and records history`() =
        runTest {
            api.operationsResponse = FakeAlphaAiApi.ok(Fixtures.operations())
            val result = systemRepo().snapshot()

            assertTrue(result is AppResult.Success)
            assertEquals("USA: open", (result as AppResult.Success).data.currentSession)
            assertEquals(1, historyDao.store.size)
            assertEquals(listOf("AAPL", "MSFT"), historyDao.store.values.first().topTickers)
        }

    @Test
    fun `snapshot offline falls back to cached snapshot`() =
        runTest {
            api.operationsResponse = FakeAlphaAiApi.ok(Fixtures.operations())
            systemRepo().snapshot()

            api.failWith = FakeAlphaAiApi.offline()
            val result = systemRepo().snapshot()

            assertTrue(result is AppResult.Offline)
            assertEquals("USA: open", (result as AppResult.Offline).data.currentSession)
        }

    @Test
    fun `market status maps clock`() =
        runTest {
            api.marketStatusResponse =
                FakeAlphaAiApi.ok(
                    com.alphaai.app.data.remote.dto.MarketStatusDto(
                        currentSession = "Europa: open",
                        openMarkets = listOf("europe"),
                        markets =
                            listOf(
                                com.alphaai.app.data.remote.dto.MarketStateDto(
                                    key = "europe", title = "Europa", isOpen = true,
                                ),
                            ),
                    ),
                )
            val result = MarketRepository(api).marketStatus()
            assertTrue(result is AppResult.Success)
            assertEquals("Europa: open", (result as AppResult.Success).data.currentSession)
        }

    @Test
    fun `discovery maps statistics`() =
        runTest {
            api.discoveryResponse =
                FakeAlphaAiApi.ok(
                    DiscoveryReportDto(
                        opportunities = listOf(Fixtures.opportunity("NVDA")),
                        statistics = DiscoveryStatisticsDto(universeCount = 100, analyzedCount = 60),
                        markets = listOf("nasdaq100"),
                    ),
                )
            val result = MarketRepository(api).discovery()
            assertTrue(result is AppResult.Success)
            val status = (result as AppResult.Success).data
            assertEquals(100, status.universeCount)
            assertEquals(1, status.opportunityCount)
        }

    @Test
    fun `history repository returns mapped entries`() =
        runTest {
            api.operationsResponse = FakeAlphaAiApi.ok(Fixtures.operations())
            systemRepo().snapshot()

            val entries = HistoryRepository(historyDao).recent()
            assertEquals(1, entries.size)
            assertEquals("USA: open", entries.first().session)
        }
}
