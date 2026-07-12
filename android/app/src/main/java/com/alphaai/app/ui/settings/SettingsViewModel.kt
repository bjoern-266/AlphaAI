package com.alphaai.app.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.alphaai.app.data.settings.AppSettings
import com.alphaai.app.data.settings.SettingsGateway
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Zustand der Einstellungs-Seite. */
data class SettingsUiState(
    val settings: AppSettings? = null,
)

/**
 * ViewModel der Einstellungs-Seite. Liest/schreibt die Verbindungs- und
 * Darstellungsoptionen. Keine Fachlogik.
 */
class SettingsViewModel(
    private val repository: SettingsGateway,
) : ViewModel() {
    private val _state = MutableStateFlow(SettingsUiState())
    val state: StateFlow<SettingsUiState> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            repository.settings.collect { settings ->
                _state.update { it.copy(settings = settings) }
            }
        }
    }

    fun setBackendUrl(value: String) = launch { repository.setBackendUrl(value) }

    fun setAutoRefresh(value: Boolean) = launch { repository.setAutoRefresh(value) }

    fun setDarkTheme(value: Boolean) = launch { repository.setDarkTheme(value) }

    fun setBackgroundRefresh(value: Boolean) = launch { repository.setBackgroundRefresh(value) }

    fun setDebug(value: Boolean) = launch { repository.setDebug(value) }

    private fun launch(block: suspend () -> Unit) {
        viewModelScope.launch { block() }
    }
}
