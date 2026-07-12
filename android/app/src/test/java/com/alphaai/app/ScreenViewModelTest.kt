package com.alphaai.app

import com.alphaai.app.data.remote.dto.MarketStatusDto
import com.alphaai.app.data.repository.HistoryRepository
import com.alphaai.app.data.repository.MarketRepository
import com.alphaai.app.data.repository.OpportunityRepository
import com.alphaai.app.data.repository.SystemRepository
import com.alphaai.app.fake.FakeAlphaAiApi
import com.alphaai.app.fake.FakeOpportunityDao
import com.alphaai.app.fake.FakeScanHistoryDao
import com.alphaai.app.fake.FakeSettingsGateway
import com.alphaai.app.fake.FakeSnapshotDao
import com.alphaai.app.fake.Fixtures
import com.alphaai.app.ui.detail.DetailViewModel
import com.alphaai.app.ui.history.HistoryViewModel
import com.alphaai.app.ui.markets.MarketsViewModel
import com.alphaai.app.ui.settings.SettingsViewModel
import com.alphaai.app.util.MainDispatcherRule
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class ScreenViewModelTest {
    @get:Rule
    val mainRule = MainDispatcherRule()

    private val api = FakeAlphaAiApi()

    @Test
    fun `detail view model loads opportunity`() =
        runTest(mainRule.dispatcher) {
            api.opportunityResponse = FakeAlphaAiApi.ok(Fixtures.opportunity("AAPL"))
            val vm =
                DetailViewModel(OpportunityRepository(api, FakeOpportunityDao(), now = { 1L }), "AAPL")
            advanceUntilIdle()
            assertNotNull(vm.state.value.opportunity)
            assertEquals("AAPL", vm.state.value.opportunity!!.ticker)
        }

    @Test
    fun `markets view model loads clock`() =
        runTest(mainRule.dispatcher) {
            api.marketStatusResponse =
                FakeAlphaAiApi.ok(MarketStatusDto(currentSession = "USA: open", openMarkets = listOf("us")))
            val vm = MarketsViewModel(MarketRepository(api))
            advanceUntilIdle()
            assertEquals("USA: open", vm.state.value.clock!!.currentSession)
        }

    @Test
    fun `history view model reads stored scans`() =
        runTest(mainRule.dispatcher) {
            val historyDao = FakeScanHistoryDao()
            val systemRepo =
                SystemRepository(
                    api,
                    FakeSnapshotDao(),
                    historyDao,
                    topTickersProvider = { listOf("AAPL") },
                    now = { 1L },
                )
            api.operationsResponse = FakeAlphaAiApi.ok(Fixtures.operations())
            systemRepo.snapshot()

            val vm = HistoryViewModel(HistoryRepository(historyDao))
            advanceUntilIdle()
            assertEquals(1, vm.state.value.entries.size)
        }

    @Test
    fun `settings view model reflects and updates settings`() =
        runTest(mainRule.dispatcher) {
            val gateway = FakeSettingsGateway()
            val vm = SettingsViewModel(gateway)
            advanceUntilIdle()
            assertTrue(vm.state.value.settings!!.darkTheme)

            vm.setDarkTheme(false)
            advanceUntilIdle()
            assertEquals(false, vm.state.value.settings!!.darkTheme)

            vm.setBackendUrl("http://192.168.1.5:8000/")
            advanceUntilIdle()
            assertEquals("http://192.168.1.5:8000/", vm.state.value.settings!!.backendUrl)
        }
}
