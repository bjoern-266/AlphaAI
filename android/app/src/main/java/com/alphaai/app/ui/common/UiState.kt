package com.alphaai.app.ui.common

/**
 * Gemeinsame Zustandsfelder eines Bildschirms.
 *
 * Bewusst keine Vererbung: jeder Bildschirm bettet diese Felder in seinen
 * eigenen, unveränderlichen UI-State ein (siehe die jeweiligen ViewModels).
 */
data class LoadStatus(
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val errorMessage: String? = null,
    val offlineReason: String? = null,
) {
    /** Ob ein Offline-Stand angezeigt wird (Cache statt frischem Scan). */
    val isOffline: Boolean get() = offlineReason != null

    /** Ob ein blockierender Fehler ohne Daten vorliegt. */
    val hasError: Boolean get() = errorMessage != null
}
