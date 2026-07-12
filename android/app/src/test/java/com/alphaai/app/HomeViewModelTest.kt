package com.alphaai.app

import com.alphaai.app.data.repository.OpportunityRepository
import com.alphaai.app.data.repository.SystemRepository
import com.alphaai.app.fake.FakeAlphaAiApi
import com.alphaai.app.fake.FakeOpportunityDao
import com.alphaai.app.fake.FakeScanHistoryDao
import com.alphaai.app.fake.FakeSnapshotDao
import com.alphaai.app.fake.Fixtures
import com.alphaai.app.ui.home.HomeViewModel
import com.alphaai.app.util.MainDispatcherRule
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Rule
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class HomeViewModelTest {
    @get:Rule
    val mainRule = MainDispatcherRule()

    private val api = FakeAlphaAiApi()

    private fun buildViewModel(): HomeViewModel {
        val systemRepo =
            SystemRepository(api, FakeSnapshotDao(), FakeScanHistoryDao(), now = { 1L })
        val oppRepo = OpportunityRepository(api, FakeOpportunityDao(), now = { 1L })
        return HomeViewModel(systemRepo, oppRepo)
    }

    @Test
    fun `loads snapshot and top opportunities`() =
        runTest(mainRule.dispatcher) {
            api.operationsResponse = FakeAlphaAiApi.ok(Fixtures.operations())
            api.topResponse = FakeAlphaAiApi.ok(listOf(Fixtures.opportunity("AAPL")))

            val vm = buildViewModel()
            advanceUntilIdle()

            val state = vm.state.value
            assertEquals(false, state.status.isLoading)
            assertNotNull(state.snapshot)
            assertEquals("USA: open", state.snapshot!!.currentSession)
            assertEquals(1, state.topOpportunities.size)
            assertNull(state.status.errorMessage)
        }

    @Test
    fun `shows error when nothing available`() =
        runTest(mainRule.dispatcher) {
            api.failWith = FakeAlphaAiApi.offline()
            val vm = buildViewModel()
            advanceUntilIdle()

            val state = vm.state.value
            assertEquals(true, state.topOpportunities.isEmpty())
            assertNotNull(state.status.errorMessage)
        }
}
