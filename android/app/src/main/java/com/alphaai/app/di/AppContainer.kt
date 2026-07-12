package com.alphaai.app.di

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.PreferenceDataStoreFactory
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.preferencesDataStoreFile
import androidx.room.Room
import com.alphaai.app.BuildConfig
import com.alphaai.app.data.local.AlphaAiDatabase
import com.alphaai.app.data.remote.ApiFactory
import com.alphaai.app.data.remote.HostSelectionInterceptor
import com.alphaai.app.data.repository.HistoryRepository
import com.alphaai.app.data.repository.MarketRepository
import com.alphaai.app.data.repository.OpportunityRepository
import com.alphaai.app.data.repository.SystemRepository
import com.alphaai.app.data.settings.SettingsRepository

/**
 * Manuelle Dependency-Injection (Composition Root der App).
 *
 * Bündelt die Erzeugung aller langlebigen Objekte (API-Client, Datenbank,
 * Repositories, Einstellungen) an einer Stelle. Bewusst ohne DI-Framework –
 * einfach, transparent und gut testbar.
 */
class AppContainer(context: Context) {
    private val appContext = context.applicationContext

    private val dataStore: DataStore<Preferences> =
        PreferenceDataStoreFactory.create(
            produceFile = { appContext.preferencesDataStoreFile("alphaai_settings") },
        )

    val settingsRepository: SettingsRepository =
        SettingsRepository(dataStore, BuildConfig.DEFAULT_BACKEND_URL)

    val hostInterceptor: HostSelectionInterceptor =
        HostSelectionInterceptor(BuildConfig.DEFAULT_BACKEND_URL)

    private val api =
        ApiFactory.create(hostInterceptor, enableLogging = BuildConfig.DEBUG)

    private val database: AlphaAiDatabase =
        Room.databaseBuilder(appContext, AlphaAiDatabase::class.java, AlphaAiDatabase.NAME)
            .fallbackToDestructiveMigration()
            .build()

    val opportunityRepository: OpportunityRepository =
        OpportunityRepository(api, database.opportunityDao())

    val marketRepository: MarketRepository = MarketRepository(api)

    val systemRepository: SystemRepository =
        SystemRepository(
            api = api,
            snapshotDao = database.snapshotDao(),
            historyDao = database.scanHistoryDao(),
            topTickersProvider = {
                database.opportunityDao().all().sortedBy { it.rank }.take(TOP_HISTORY).map { it.ticker }
            },
        )

    val historyRepository: HistoryRepository =
        HistoryRepository(database.scanHistoryDao())

    /** Übernimmt eine geänderte Backend-Adresse in den Netzwerk-Client. */
    fun applyBackendUrl(url: String) = hostInterceptor.setBaseUrl(url)

    private companion object {
        const val TOP_HISTORY = 10
    }
}
