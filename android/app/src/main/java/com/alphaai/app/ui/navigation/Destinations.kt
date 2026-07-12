package com.alphaai.app.ui.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Insights
import androidx.compose.material.icons.filled.Public
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Timeline
import androidx.compose.ui.graphics.vector.ImageVector

/** Alle Navigationsziele der App (Routen + Bottom-Navigation). */
sealed class Destination(val route: String) {
    /** Ziele der unteren Navigationsleiste. */
    sealed class Tab(
        route: String,
        val label: String,
        val icon: ImageVector,
    ) : Destination(route)

    data object Home : Tab("home", "Home", Icons.Filled.Home)

    data object Opportunities : Tab("opportunities", "Chancen", Icons.Filled.Insights)

    data object Markets : Tab("markets", "Märkte", Icons.Filled.Public)

    data object History : Tab("history", "Verlauf", Icons.Filled.Timeline)

    data object Settings : Tab("settings", "Einstellungen", Icons.Filled.Settings)

    /** Detailseite einer Chance (Ticker als Pfadargument). */
    data object Detail : Destination("detail/{ticker}") {
        const val ARG_TICKER = "ticker"

        /** Baut die konkrete Route zu einem Ticker. */
        fun route(ticker: String): String = "detail/$ticker"
    }

    companion object {
        /** Die Reihenfolge der Tabs in der Bottom-Navigation. */
        val tabs: List<Tab> = listOf(Home, Opportunities, Markets, History, Settings)
    }
}
