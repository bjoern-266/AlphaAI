package com.alphaai.app.data.settings

import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/** Benutzereinstellungen der App (nur Anzeige-/Verbindungsoptionen). */
data class AppSettings(
    val backendUrl: String,
    val autoRefresh: Boolean,
    val darkTheme: Boolean,
    val backgroundRefresh: Boolean,
    val debug: Boolean,
)

/**
 * Vertrag der Einstellungsquelle (erlaubt Test-Doubles ohne DataStore).
 */
interface SettingsGateway {
    /** Beobachtbarer Strom der aktuellen Einstellungen. */
    val settings: Flow<AppSettings>

    suspend fun setBackendUrl(value: String)

    suspend fun setAutoRefresh(value: Boolean)

    suspend fun setDarkTheme(value: Boolean)

    suspend fun setBackgroundRefresh(value: Boolean)

    suspend fun setDebug(value: Boolean)
}

/**
 * Persistiert die Benutzereinstellungen über Jetpack DataStore.
 *
 * Enthält keine Fachlogik – ausschließlich Verbindungs-/Darstellungsoptionen
 * (Backend-Adresse, Auto-Refresh, Theme, Cache/Debug).
 */
class SettingsRepository(
    private val dataStore: DataStore<Preferences>,
    private val defaultBackendUrl: String,
) : SettingsGateway {
    /** Beobachtbarer Strom der aktuellen Einstellungen. */
    override val settings: Flow<AppSettings> =
        dataStore.data.map { prefs ->
            AppSettings(
                backendUrl = prefs[BACKEND_URL] ?: defaultBackendUrl,
                autoRefresh = prefs[AUTO_REFRESH] ?: true,
                darkTheme = prefs[DARK_THEME] ?: true,
                backgroundRefresh = prefs[BACKGROUND_REFRESH] ?: false,
                debug = prefs[DEBUG] ?: false,
            )
        }

    override suspend fun setBackendUrl(value: String) = edit(BACKEND_URL, value.trim())

    override suspend fun setAutoRefresh(value: Boolean) = edit(AUTO_REFRESH, value)

    override suspend fun setDarkTheme(value: Boolean) = edit(DARK_THEME, value)

    override suspend fun setBackgroundRefresh(value: Boolean) = edit(BACKGROUND_REFRESH, value)

    override suspend fun setDebug(value: Boolean) = edit(DEBUG, value)

    private suspend fun <T> edit(
        key: Preferences.Key<T>,
        value: T,
    ) {
        dataStore.edit { it[key] = value }
    }

    private companion object {
        val BACKEND_URL = stringPreferencesKey("backend_url")
        val AUTO_REFRESH = booleanPreferencesKey("auto_refresh")
        val DARK_THEME = booleanPreferencesKey("dark_theme")
        val BACKGROUND_REFRESH = booleanPreferencesKey("background_refresh")
        val DEBUG = booleanPreferencesKey("debug")
    }
}
