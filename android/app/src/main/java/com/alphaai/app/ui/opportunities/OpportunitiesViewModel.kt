package com.alphaai.app.ui.opportunities

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.alphaai.app.core.AppResult
import com.alphaai.app.core.dataOrNull
import com.alphaai.app.data.repository.OpportunityRepository
import com.alphaai.app.domain.model.Direction
import com.alphaai.app.domain.model.Opportunity
import com.alphaai.app.ui.common.LoadStatus
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Sortierkriterien der Chancenliste (nur Anzeige-Reihenfolge). */
enum class SortMode(val label: String) {
    SCORE("Score"),
    CONFIDENCE("Confidence"),
    RISK("Risk"),
    RANK("Rang"),
}

/** Aktive Filter/Sortierung der Chancenliste. */
data class OpportunityFilter(
    val query: String = "",
    val direction: Direction? = null,
    val market: String? = null,
    val sector: String? = null,
    val sort: SortMode = SortMode.SCORE,
)

/** Zustand der Chancen-Seite. */
data class OpportunitiesUiState(
    val status: LoadStatus = LoadStatus(isLoading = true),
    val all: List<Opportunity> = emptyList(),
    val visible: List<Opportunity> = emptyList(),
    val filter: OpportunityFilter = OpportunityFilter(),
    val markets: List<String> = emptyList(),
    val sectors: List<String> = emptyList(),
)

/**
 * ViewModel der Chancen-Seite. Lädt alle Chancen aus der REST-API und wendet
 * lokal **nur Anzeige-Filter/Sortierung** an – es werden keine Kennzahlen
 * berechnet oder verändert.
 */
class OpportunitiesViewModel(
    private val repository: OpportunityRepository,
) : ViewModel() {
    private val _state = MutableStateFlow(OpportunitiesUiState())
    val state: StateFlow<OpportunitiesUiState> = _state.asStateFlow()

    init {
        load(initial = true)
    }

    fun refresh() = load(initial = false)

    fun setQuery(query: String) = updateFilter { it.copy(query = query) }

    fun setDirection(direction: Direction?) = updateFilter { it.copy(direction = direction) }

    fun setMarket(market: String?) = updateFilter { it.copy(market = market) }

    fun setSector(sector: String?) = updateFilter { it.copy(sector = sector) }

    fun setSort(sort: SortMode) = updateFilter { it.copy(sort = sort) }

    fun clearFilters() = updateFilter { OpportunityFilter() }

    private fun load(initial: Boolean) {
        _state.update {
            it.copy(status = it.status.copy(isLoading = initial, isRefreshing = !initial, errorMessage = null))
        }
        viewModelScope.launch {
            val result = repository.opportunities()
            val data = result.dataOrNull()
            _state.update { current ->
                if (data == null) {
                    current.copy(
                        status =
                            LoadStatus(
                                errorMessage =
                                    (result as? AppResult.Failure)?.error?.message
                                        ?: "Keine Verbindung zum Backend.",
                            ),
                    )
                } else {
                    current
                        .copy(
                            status = LoadStatus(offlineReason = (result as? AppResult.Offline)?.reason),
                            all = data,
                            markets = data.map { it.market }.filter { it.isNotBlank() }.distinct().sorted(),
                            sectors = data.map { it.sector }.filter { it.isNotBlank() }.distinct().sorted(),
                        )
                        .withRecomputedVisible()
                }
            }
        }
    }

    private fun updateFilter(transform: (OpportunityFilter) -> OpportunityFilter) {
        _state.update { it.copy(filter = transform(it.filter)).withRecomputedVisible() }
    }

    private fun OpportunitiesUiState.withRecomputedVisible(): OpportunitiesUiState =
        copy(visible = applyFilter(all, filter))

    private companion object {
        fun applyFilter(
            items: List<Opportunity>,
            filter: OpportunityFilter,
        ): List<Opportunity> {
            val query = filter.query.trim().uppercase()
            val filtered =
                items.filter { opportunity ->
                    (filter.direction == null || opportunity.direction == filter.direction) &&
                        (filter.market == null || opportunity.market == filter.market) &&
                        (filter.sector == null || opportunity.sector == filter.sector) &&
                        (
                            query.isEmpty() ||
                                opportunity.ticker.uppercase().contains(query) ||
                                opportunity.company.uppercase().contains(query)
                        )
                }
            return when (filter.sort) {
                SortMode.SCORE -> filtered.sortedByDescending { it.opportunityScore ?: -1.0 }
                SortMode.CONFIDENCE -> filtered.sortedByDescending { it.confidence ?: -1.0 }
                SortMode.RISK -> filtered.sortedByDescending { it.risk ?: -1.0 }
                SortMode.RANK -> filtered.sortedBy { if (it.rank > 0) it.rank else Int.MAX_VALUE }
            }
        }
    }
}
