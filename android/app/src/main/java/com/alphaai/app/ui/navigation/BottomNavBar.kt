package com.alphaai.app.ui.navigation

import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavHostController
import androidx.navigation.compose.currentBackStackEntryAsState
import com.alphaai.app.ui.theme.AlphaColors

/** Untere Navigationsleiste mit den fünf Hauptbereichen. */
@Composable
fun BottomNavBar(navController: NavHostController) {
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination = backStackEntry?.destination

    NavigationBar(containerColor = AlphaColors.CarbonElevated) {
        Destination.tabs.forEach { tab ->
            val selected = currentDestination?.hierarchy?.any { it.route == tab.route } == true
            NavigationBarItem(
                modifier = Modifier.testTag("tab_${tab.route}"),
                selected = selected,
                onClick = { navController.navigateToTab(tab) },
                icon = { Icon(tab.icon, contentDescription = tab.label) },
                label = { Text(tab.label) },
                colors =
                    NavigationBarItemDefaults.colors(
                        selectedIconColor = AlphaColors.OnAmber,
                        selectedTextColor = AlphaColors.Amber,
                        indicatorColor = AlphaColors.Amber,
                        unselectedIconColor = AlphaColors.TextSecondary,
                        unselectedTextColor = AlphaColors.TextMuted,
                    ),
            )
        }
    }
}

private fun NavHostController.navigateToTab(tab: Destination.Tab) {
    navigate(tab.route) {
        popUpTo(graph.startDestinationId) { saveState = true }
        launchSingleTop = true
        restoreState = true
    }
}
