package com.alphaai.app.ui.detail

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.alphaai.app.core.AppResult
import com.alphaai.app.core.dataOrNull
import com.alphaai.app.data.repository.OpportunityRepository
import com.alphaai.app.domain.model.Opportunity
import com.alphaai.app.ui.common.LoadStatus
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Zustand der Detailseite einer Chance. */
data class DetailUiState(
    val status: LoadStatus = LoadStatus(isLoading = true),
    val ticker: String = "",
    val opportunity: Opportunity? = null,
)

/**
 * ViewModel der Detailseite. Lädt eine einzelne Chance aus der REST-API
 * (Opportunity- oder Empfehlungs-Endpunkt) mit Offline-Fallback.
 */
class DetailViewModel(
    private val repository: OpportunityRepository,
    private val ticker: String,
) : ViewModel() {
    private val _state = MutableStateFlow(DetailUiState(ticker = ticker))
    val state: StateFlow<DetailUiState> = _state.asStateFlow()

    init {
        load()
    }

    /** Lädt (bzw. aktualisiert) die Detaildaten. */
    fun load() {
        _state.update { it.copy(status = it.status.copy(isLoading = true, errorMessage = null)) }
        viewModelScope.launch {
            val result = repository.detail(ticker)
            val data = result.dataOrNull()
            _state.update {
                it.copy(
                    status =
                        LoadStatus(
                            errorMessage =
                                if (data == null) {
                                    (result as? AppResult.Failure)?.error?.message
                                        ?: "Keine Daten verfügbar."
                                } else {
                                    null
                                },
                            offlineReason = (result as? AppResult.Offline)?.reason,
                        ),
                    opportunity = data ?: it.opportunity,
                )
            }
        }
    }
}
