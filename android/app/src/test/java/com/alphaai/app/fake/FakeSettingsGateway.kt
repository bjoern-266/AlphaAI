package com.alphaai.app.fake

import com.alphaai.app.data.settings.AppSettings
import com.alphaai.app.data.settings.SettingsGateway
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow

/** In-Memory-Ersatz für [SettingsGateway]. */
class FakeSettingsGateway(
    initial: AppSettings =
        AppSettings(
            backendUrl = "http://localhost:8000/",
            autoRefresh = true,
            darkTheme = true,
            backgroundRefresh = false,
            debug = false,
        ),
) : SettingsGateway {
    private val state = MutableStateFlow(initial)
    override val settings: Flow<AppSettings> = state

    override suspend fun setBackendUrl(value: String) {
        state.value = state.value.copy(backendUrl = value)
    }

    override suspend fun setAutoRefresh(value: Boolean) {
        state.value = state.value.copy(autoRefresh = value)
    }

    override suspend fun setDarkTheme(value: Boolean) {
        state.value = state.value.copy(darkTheme = value)
    }

    override suspend fun setBackgroundRefresh(value: Boolean) {
        state.value = state.value.copy(backgroundRefresh = value)
    }

    override suspend fun setDebug(value: Boolean) {
        state.value = state.value.copy(debug = value)
    }
}
