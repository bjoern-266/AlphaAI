package com.alphaai.app

import com.alphaai.app.data.remote.dto.OpportunityReportDto
import com.alphaai.app.data.repository.OpportunityRepository
import com.alphaai.app.domain.model.Direction
import com.alphaai.app.fake.FakeAlphaAiApi
import com.alphaai.app.fake.FakeOpportunityDao
import com.alphaai.app.fake.Fixtures
import com.alphaai.app.ui.opportunities.OpportunitiesViewModel
import com.alphaai.app.ui.opportunities.SortMode
import com.alphaai.app.util.MainDispatcherRule
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class OpportunitiesViewModelTest {
    @get:Rule
    val mainRule = MainDispatcherRule()

    private val api = FakeAlphaAiApi()

    private fun viewModel(): OpportunitiesViewModel {
        api.opportunitiesResponse =
            FakeAlphaAiApi.ok(
                OpportunityReportDto(
                    opportunities =
                        listOf(
                            Fixtures.opportunity("AAPL", score = 90.0, direction = "long", rank = 1),
                            Fixtures.opportunity("MSFT", score = 70.0, direction = "long", rank = 2),
                            Fixtures.opportunity("XOM", score = 60.0, direction = "short", rank = 3),
                        ),
                ),
            )
        return OpportunitiesViewModel(OpportunityRepository(api, FakeOpportunityDao(), now = { 1L }))
    }

    @Test
    fun `loads and sorts by score by default`() =
        runTest(mainRule.dispatcher) {
            val vm = viewModel()
            advanceUntilIdle()
            val visible = vm.state.value.visible
            assertEquals(3, visible.size)
            assertEquals("AAPL", visible.first().ticker)
        }

    @Test
    fun `filters by direction`() =
        runTest(mainRule.dispatcher) {
            val vm = viewModel()
            advanceUntilIdle()
            vm.setDirection(Direction.SHORT)
            assertEquals(listOf("XOM"), vm.state.value.visible.map { it.ticker })
        }

    @Test
    fun `search filters by ticker`() =
        runTest(mainRule.dispatcher) {
            val vm = viewModel()
            advanceUntilIdle()
            vm.setQuery("msf")
            assertEquals(listOf("MSFT"), vm.state.value.visible.map { it.ticker })
        }

    @Test
    fun `sort by risk reorders`() =
        runTest(mainRule.dispatcher) {
            val vm = viewModel()
            advanceUntilIdle()
            vm.setSort(SortMode.RANK)
            assertEquals(listOf("AAPL", "MSFT", "XOM"), vm.state.value.visible.map { it.ticker })
        }

    @Test
    fun `clear filters restores all`() =
        runTest(mainRule.dispatcher) {
            val vm = viewModel()
            advanceUntilIdle()
            vm.setDirection(Direction.SHORT)
            vm.clearFilters()
            assertEquals(3, vm.state.value.visible.size)
        }

    @Test
    fun `derives available markets`() =
        runTest(mainRule.dispatcher) {
            val vm = viewModel()
            advanceUntilIdle()
            assertEquals(listOf("NASDAQ"), vm.state.value.markets)
        }
}
