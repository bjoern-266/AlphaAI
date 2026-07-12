package com.alphaai.app.ui.markets

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.alphaai.app.core.AppResult
import com.alphaai.app.core.dataOrNull
import com.alphaai.app.data.repository.MarketRepository
import com.alphaai.app.domain.model.DiscoveryStatus
import com.alphaai.app.domain.model.MarketClock
import com.alphaai.app.ui.common.LoadStatus
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Zustand der Märkte-Seite (Marktuhr + Discovery-Zustand). */
data class MarketsUiState(
    val status: LoadStatus = LoadStatus(isLoading = true),
    val clock: MarketClock? = null,
    val discovery: DiscoveryStatus? = null,
)

/** ViewModel der Märkte-Seite. Liest Marktuhr und Discovery-Zustand. */
class MarketsViewModel(
    private val repository: MarketRepository,
) : ViewModel() {
    private val _state = MutableStateFlow(MarketsUiState())
    val state: StateFlow<MarketsUiState> = _state.asStateFlow()

    init {
        load(initial = true)
    }

    fun refresh() = load(initial = false)

    private fun load(initial: Boolean) {
        _state.update {
            it.copy(status = it.status.copy(isLoading = initial, isRefreshing = !initial, errorMessage = null))
        }
        viewModelScope.launch {
            val (clockResult, discoveryResult) =
                coroutineScope {
                    val clock = async { repository.marketStatus() }
                    val discovery = async { repository.discovery() }
                    clock.await() to discovery.await()
                }
            val clock = clockResult.dataOrNull()
            _state.update {
                it.copy(
                    status =
                        LoadStatus(
                            errorMessage =
                                if (clock == null) {
                                    (clockResult as? AppResult.Failure)?.error?.message
                                        ?: "Keine Verbindung zum Backend."
                                } else {
                                    null
                                },
                            offlineReason = (clockResult as? AppResult.Offline)?.reason,
                        ),
                    clock = clock ?: it.clock,
                    discovery = discoveryResult.dataOrNull() ?: it.discovery,
                )
            }
        }
    }
}
