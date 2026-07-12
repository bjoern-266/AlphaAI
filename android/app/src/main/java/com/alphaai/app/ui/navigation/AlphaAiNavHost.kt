package com.alphaai.app.ui.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.alphaai.app.di.AppContainer
import com.alphaai.app.ui.detail.DetailScreen
import com.alphaai.app.ui.detail.DetailViewModel
import com.alphaai.app.ui.history.HistoryScreen
import com.alphaai.app.ui.history.HistoryViewModel
import com.alphaai.app.ui.home.HomeScreen
import com.alphaai.app.ui.home.HomeViewModel
import com.alphaai.app.ui.markets.MarketsScreen
import com.alphaai.app.ui.markets.MarketsViewModel
import com.alphaai.app.ui.opportunities.OpportunitiesScreen
import com.alphaai.app.ui.opportunities.OpportunitiesViewModel
import com.alphaai.app.ui.settings.SettingsScreen
import com.alphaai.app.ui.settings.SettingsViewModel

/**
 * Wurzel-Navigation der App: Gerüst mit Bottom-Navigation und den fünf
 * Hauptbereichen plus der Detailseite. ViewModels werden über die manuelle
 * DI ([AppContainer]) erzeugt.
 */
@Composable
fun AlphaAiNavHost(container: AppContainer) {
    val navController = rememberNavController()

    Scaffold(
        bottomBar = { BottomNavBar(navController) },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = Destination.Home.route,
            modifier = Modifier.padding(padding),
        ) {
            composable(Destination.Home.route) {
                val vm: HomeViewModel =
                    viewModel(
                        factory =
                            viewModelFactory {
                                initializer {
                                    HomeViewModel(
                                        container.systemRepository,
                                        container.opportunityRepository,
                                    )
                                }
                            },
                    )
                HomeScreen(
                    viewModel = vm,
                    onOpportunityClick = { navController.navigate(Destination.Detail.route(it)) },
                    onSeeAllOpportunities = { navController.navigate(Destination.Opportunities.route) },
                )
            }

            composable(Destination.Opportunities.route) {
                val vm: OpportunitiesViewModel =
                    viewModel(
                        factory =
                            viewModelFactory {
                                initializer { OpportunitiesViewModel(container.opportunityRepository) }
                            },
                    )
                OpportunitiesScreen(
                    viewModel = vm,
                    onOpportunityClick = { navController.navigate(Destination.Detail.route(it)) },
                )
            }

            composable(Destination.Markets.route) {
                val vm: MarketsViewModel =
                    viewModel(
                        factory =
                            viewModelFactory {
                                initializer { MarketsViewModel(container.marketRepository) }
                            },
                    )
                MarketsScreen(viewModel = vm)
            }

            composable(Destination.History.route) {
                val vm: HistoryViewModel =
                    viewModel(
                        factory =
                            viewModelFactory {
                                initializer { HistoryViewModel(container.historyRepository) }
                            },
                    )
                HistoryScreen(viewModel = vm)
            }

            composable(Destination.Settings.route) {
                val vm: SettingsViewModel =
                    viewModel(
                        factory =
                            viewModelFactory {
                                initializer { SettingsViewModel(container.settingsRepository) }
                            },
                    )
                SettingsScreen(viewModel = vm)
            }

            composable(
                route = Destination.Detail.route,
                arguments = listOf(navArgument(Destination.Detail.ARG_TICKER) { type = NavType.StringType }),
            ) { entry ->
                val ticker = entry.arguments?.getString(Destination.Detail.ARG_TICKER).orEmpty()
                val vm: DetailViewModel =
                    viewModel(
                        factory =
                            viewModelFactory {
                                initializer { DetailViewModel(container.opportunityRepository, ticker) }
                            },
                    )
                DetailScreen(viewModel = vm, onBack = { navController.popBackStack() })
            }
        }
    }
}
