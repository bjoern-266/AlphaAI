package com.alphaai.app

import android.app.Application
import com.alphaai.app.di.AppContainer
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch

/**
 * Anwendungsklasse: erzeugt den [AppContainer] und hält die Backend-Adresse des
 * Netzwerk-Clients mit den Einstellungen synchron.
 */
class AlphaAiApplication : Application() {
    lateinit var container: AppContainer
        private set

    private val appScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
        observeBackendUrl()
    }

    private fun observeBackendUrl() {
        appScope.launch {
            container.settingsRepository.settings
                .map { it.backendUrl }
                .distinctUntilChanged()
                .collect { url -> container.applyBackendUrl(url) }
        }
    }
}
