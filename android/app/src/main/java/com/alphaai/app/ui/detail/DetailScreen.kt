package com.alphaai.app.ui.detail

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.alphaai.app.domain.model.Opportunity
import com.alphaai.app.ui.common.Format
import com.alphaai.app.ui.components.DirectionBadge
import com.alphaai.app.ui.components.ErrorView
import com.alphaai.app.ui.components.LoadingView
import com.alphaai.app.ui.components.OfflineBanner
import com.alphaai.app.ui.components.StatChip
import com.alphaai.app.ui.components.StrengthBadge
import com.alphaai.app.ui.theme.AlphaColors

/** Detailseite: vollständige, unveränderte Analyse einer Chance. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DetailScreen(
    viewModel: DetailViewModel,
    onBack: () -> Unit,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(state.ticker) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Zurück")
                    }
                },
            )
        },
    ) { padding ->
        val opportunity = state.opportunity
        when {
            state.status.isLoading && opportunity == null ->
                LoadingView(Modifier.padding(padding))
            opportunity == null ->
                ErrorView(state.status.errorMessage.orEmpty(), viewModel::load, Modifier.padding(padding))
            else ->
                DetailContent(
                    opportunity = opportunity,
                    offlineReason = state.status.offlineReason,
                    modifier = Modifier.padding(padding),
                )
        }
    }
}

@Composable
private fun DetailContent(
    opportunity: Opportunity,
    offlineReason: String?,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
    ) {
        offlineReason?.let { OfflineBanner(it) }

        Text(
            text = opportunity.company.ifBlank { opportunity.ticker },
            style = MaterialTheme.typography.headlineMedium,
            color = AlphaColors.TextPrimary,
            fontWeight = FontWeight.Bold,
        )
        Text(
            text = "${opportunity.market} · ${opportunity.sector}",
            color = AlphaColors.TextSecondary,
            modifier = Modifier.padding(top = 4.dp),
        )

        Row(
            modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            DirectionBadge(opportunity.direction)
            StrengthBadge(opportunity.strength)
        }

        Row(
            modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            StatChip("Opportunity Score", Format.score(opportunity.opportunityScore))
            StatChip("Confidence", Format.percent(opportunity.confidence))
            StatChip("Risk", Format.risk(opportunity.risk))
        }

        InfoCard("Summary", opportunity.summary)
        ListCard("Reasons", opportunity.reasons)
        ListCard("Warnings", opportunity.warnings)
        InfoCard("Pattern", opportunity.patternSummary)
        InfoCard("Strategien", opportunity.strategySummary)
        InfoCard("Analytics", opportunity.analyticsSummary)
        InfoCard("Backtest", opportunity.backtestSummary)
        InfoCard("Paper Trading", opportunity.paperTradingSummary)
        InfoCard("Market Intelligence", opportunity.marketIntelligenceSummary)
        InfoCard("Zeitpunkt Analyse", Format.timestamp(opportunity.analyzedAt))
    }
}

@Composable
private fun InfoCard(
    title: String,
    body: String,
) {
    if (body.isBlank()) return
    Card(
        modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
        colors = CardDefaults.cardColors(containerColor = AlphaColors.CarbonCard),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(title, color = AlphaColors.Amber, fontWeight = FontWeight.SemiBold)
            Text(
                text = body,
                color = AlphaColors.TextSecondary,
                modifier = Modifier.padding(top = 6.dp),
            )
        }
    }
}

@Composable
private fun ListCard(
    title: String,
    items: List<String>,
) {
    if (items.isEmpty()) return
    Card(
        modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
        colors = CardDefaults.cardColors(containerColor = AlphaColors.CarbonCard),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(title, color = AlphaColors.Amber, fontWeight = FontWeight.SemiBold)
            items.forEach { item ->
                Text(
                    text = "• $item",
                    color = AlphaColors.TextSecondary,
                    modifier = Modifier.padding(top = 6.dp),
                )
            }
        }
    }
}
