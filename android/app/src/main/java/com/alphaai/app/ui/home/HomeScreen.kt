package com.alphaai.app.ui.home

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
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.alphaai.app.domain.model.OperationSnapshot
import com.alphaai.app.ui.common.Format
import com.alphaai.app.ui.components.ErrorView
import com.alphaai.app.ui.components.HealthBadge
import com.alphaai.app.ui.components.LoadingView
import com.alphaai.app.ui.components.MarketStatusCard
import com.alphaai.app.ui.components.OfflineBanner
import com.alphaai.app.ui.components.OpportunityCard
import com.alphaai.app.ui.components.SectionHeader
import com.alphaai.app.ui.components.StatChip
import com.alphaai.app.ui.theme.AlphaColors

/** Startseite: sofortiger Überblick über Markt, Scans und Top-Chancen. */
@Composable
fun HomeScreen(
    viewModel: HomeViewModel,
    onOpportunityClick: (String) -> Unit,
    onSeeAllOpportunities: () -> Unit,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    when {
        state.status.isLoading && state.snapshot == null && state.topOpportunities.isEmpty() ->
            LoadingView()
        state.status.hasError && state.snapshot == null && state.topOpportunities.isEmpty() ->
            ErrorView(message = state.status.errorMessage.orEmpty(), onRetry = viewModel::refresh)
        else ->
            HomeContent(
                state = state,
                onOpportunityClick = onOpportunityClick,
                onSeeAll = onSeeAllOpportunities,
            )
    }
}

@Composable
private fun HomeContent(
    state: HomeUiState,
    onOpportunityClick: (String) -> Unit,
    onSeeAll: () -> Unit,
) {
    LazyColumn(modifier = Modifier.fillMaxSize().testTag("home_list")) {
        state.status.offlineReason?.let { reason ->
            item { OfflineBanner(reason) }
        }

        state.snapshot?.let { snapshot ->
            item { MarketSummaryCard(snapshot) }
            items(snapshot.markets, key = { it.key }) { market ->
                MarketStatusCard(market)
            }
            item { SignalsCard(snapshot) }
        }

        item {
            Row(
                modifier = Modifier.fillMaxWidth().padding(end = 8.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                SectionHeader("Top Chancen")
                TextButton(onClick = onSeeAll) { Text("Alle") }
            }
        }
        items(state.topOpportunities, key = { it.ticker }) { opportunity ->
            OpportunityCard(opportunity = opportunity, onClick = { onOpportunityClick(opportunity.ticker) })
        }

        item { androidx.compose.foundation.layout.Spacer(Modifier.padding(12.dp)) }
    }
}

@Composable
private fun MarketSummaryCard(snapshot: OperationSnapshot) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(16.dp),
        colors = CardDefaults.cardColors(containerColor = AlphaColors.CarbonElevated),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(
                    text = snapshot.currentSession.ifBlank { "Marktstatus" },
                    style = MaterialTheme.typography.titleLarge,
                    color = AlphaColors.TextPrimary,
                    fontWeight = FontWeight.Bold,
                )
                HealthBadge(snapshot.health)
            }
            Row(
                modifier = Modifier.fillMaxWidth().padding(top = 14.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                StatChip("Letzter Scan", Format.timestamp(snapshot.lastScanAt))
                StatChip("Nächster Scan", Format.timestamp(snapshot.nextScanAt))
            }
            Row(
                modifier = Modifier.fillMaxWidth().padding(top = 10.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                StatChip("Scans", snapshot.scanCount.toString())
                StatChip("Offene Börsen", snapshot.openMarkets.size.toString())
                StatChip("Nächste Öffnung", snapshot.nextOpenMarket.ifBlank { "—" })
            }
        }
    }
}

@Composable
private fun SignalsCard(snapshot: OperationSnapshot) {
    if (snapshot.newOpportunities.isEmpty() && snapshot.newRisks.isEmpty()) return
    Card(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp),
        colors = CardDefaults.cardColors(containerColor = AlphaColors.CarbonCard),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            if (snapshot.newOpportunities.isNotEmpty()) {
                Text("Neue Chancen", color = AlphaColors.Long, fontWeight = FontWeight.SemiBold)
                Text(
                    text = snapshot.newOpportunities.joinToString(" · "),
                    color = AlphaColors.TextSecondary,
                    modifier = Modifier.padding(top = 4.dp, bottom = 8.dp),
                )
            }
            if (snapshot.newRisks.isNotEmpty()) {
                Text("Neue Risiken", color = AlphaColors.Short, fontWeight = FontWeight.SemiBold)
                Text(
                    text = snapshot.newRisks.joinToString(" · "),
                    color = AlphaColors.TextSecondary,
                    modifier = Modifier.padding(top = 4.dp),
                )
            }
        }
    }
}
