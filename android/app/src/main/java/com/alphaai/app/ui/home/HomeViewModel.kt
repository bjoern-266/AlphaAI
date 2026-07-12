package com.alphaai.app.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.alphaai.app.core.AppResult
import com.alphaai.app.core.Constants
import com.alphaai.app.core.dataOrNull
import com.alphaai.app.data.repository.OpportunityRepository
import com.alphaai.app.data.repository.SystemRepository
import com.alphaai.app.domain.model.OperationSnapshot
import com.alphaai.app.domain.model.Opportunity
import com.alphaai.app.ui.common.LoadStatus
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Zustand der Startseite (Marktstatus, Top-Chancen, neue Chancen/Risiken). */
data class HomeUiState(
    val status: LoadStatus = LoadStatus(isLoading = true),
    val snapshot: OperationSnapshot? = null,
    val topOpportunities: List<Opportunity> = emptyList(),
)

/**
 * ViewModel der Startseite. Lädt beim Start sofort den Marktstatus und die
 * Top-Chancen aus der REST-API (mit Offline-Fallback). Es findet **keine**
 * Berechnung statt – alle Werte stammen aus dem Backend.
 */
class HomeViewModel(
    private val systemRepository: SystemRepository,
    private val opportunityRepository: OpportunityRepository,
) : ViewModel() {
    private val _state = MutableStateFlow(HomeUiState())
    val state: StateFlow<HomeUiState> = _state.asStateFlow()

    init {
        load(initial = true)
    }

    /** Aktualisiert bei Pull-to-Refresh (ohne blockierende Ladeanzeige). */
    fun refresh() = load(initial = false)

    private fun load(initial: Boolean) {
        _state.update {
            it.copy(status = it.status.copy(isLoading = initial, isRefreshing = !initial, errorMessage = null))
        }
        viewModelScope.launch {
            val (snapshotResult, topResult) =
                coroutineScope {
                    val snapshot = async { systemRepository.snapshot() }
                    val top = async { opportunityRepository.topOpportunities(Constants.HOME_TOP_LIMIT) }
                    snapshot.await() to top.await()
                }

            val snapshot = snapshotResult.dataOrNull()
            val top = topResult.dataOrNull().orEmpty()
            val offline =
                (snapshotResult as? AppResult.Offline)?.reason
                    ?: (topResult as? AppResult.Offline)?.reason
            val error =
                if (snapshot == null && top.isEmpty()) {
                    (snapshotResult as? AppResult.Failure)?.error?.message
                        ?: "Keine Verbindung zum Backend."
                } else {
                    null
                }

            _state.update {
                it.copy(
                    status =
                        LoadStatus(
                            isLoading = false,
                            isRefreshing = false,
                            errorMessage = error,
                            offlineReason = offline,
                        ),
                    snapshot = snapshot ?: it.snapshot,
                    topOpportunities = if (top.isNotEmpty()) top else it.topOpportunities,
                )
            }
        }
    }
}
