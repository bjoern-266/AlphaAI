package com.alphaai.app.ui.history

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.alphaai.app.data.repository.HistoryRepository
import com.alphaai.app.domain.model.ScanHistoryEntry
import com.alphaai.app.ui.common.LoadStatus
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Zustand der Verlaufs-Seite (letzte Scans). */
data class HistoryUiState(
    val status: LoadStatus = LoadStatus(isLoading = true),
    val entries: List<ScanHistoryEntry> = emptyList(),
)

/** ViewModel der Verlaufs-Seite. Liest die lokal gespeicherte Scan-Historie. */
class HistoryViewModel(
    private val repository: HistoryRepository,
) : ViewModel() {
    private val _state = MutableStateFlow(HistoryUiState())
    val state: StateFlow<HistoryUiState> = _state.asStateFlow()

    init {
        load()
    }

    /** Lädt die Historie neu (aus dem lokalen Cache). */
    fun load() {
        _state.update { it.copy(status = it.status.copy(isLoading = true)) }
        viewModelScope.launch {
            val entries = repository.recent()
            _state.update {
                it.copy(status = LoadStatus(isLoading = false), entries = entries)
            }
        }
    }
}
