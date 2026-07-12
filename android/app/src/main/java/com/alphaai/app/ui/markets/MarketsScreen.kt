package com.alphaai.app.ui.markets

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.alphaai.app.domain.model.DiscoveryStatus
import com.alphaai.app.ui.components.ErrorView
import com.alphaai.app.ui.components.LoadingView
import com.alphaai.app.ui.components.MarketStatusCard
import com.alphaai.app.ui.components.OfflineBanner
import com.alphaai.app.ui.components.SectionHeader
import com.alphaai.app.ui.components.StatChip
import com.alphaai.app.ui.theme.AlphaColors

/** Märkte-Seite: Zustand von Europa/USA und der Discovery-Prozess. */
@Composable
fun MarketsScreen(viewModel: MarketsViewModel) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    when {
        state.status.isLoading && state.clock == null -> LoadingView()
        state.status.hasError && state.clock == null ->
            ErrorView(state.status.errorMessage.orEmpty(), viewModel::refresh)
        else ->
            LazyColumn(modifier = Modifier.fillMaxSize().testTag("markets_list")) {
                state.status.offlineReason?.let { item { OfflineBanner(it) } }

                state.clock?.let { clock ->
                    item {
                        Text(
                            text = clock.currentSession.ifBlank { "Aktive Session" },
                            style = MaterialTheme.typography.titleLarge,
                            color = AlphaColors.TextPrimary,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(16.dp),
                        )
                    }
                    items(clock.markets, key = { it.key }) { market ->
                        MarketStatusCard(market)
                    }
                }

                state.discovery?.let { discovery ->
                    item { SectionHeader("Discovery Status") }
                    item { DiscoveryCard(discovery) }
                }
            }
    }
}

@Composable
private fun DiscoveryCard(discovery: DiscoveryStatus) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp),
        colors = CardDefaults.cardColors(containerColor = AlphaColors.CarbonCard),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                StatChip("Universum", discovery.universeCount?.toString() ?: "—")
                StatChip("Analysiert", discovery.analyzedCount?.toString() ?: "—")
                StatChip("Verworfen", discovery.rejectedCount?.toString() ?: "—")
                StatChip("Chancen", discovery.opportunityCount.toString())
            }
            if (discovery.markets.isNotEmpty()) {
                Text(
                    text = "Märkte: ${discovery.markets.joinToString(", ")}",
                    color = AlphaColors.TextSecondary,
                    modifier = Modifier.padding(top = 12.dp),
                )
            }
        }
    }
}
