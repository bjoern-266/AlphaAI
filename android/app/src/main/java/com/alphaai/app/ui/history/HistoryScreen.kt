package com.alphaai.app.ui.history

import androidx.compose.foundation.layout.Column
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
import com.alphaai.app.domain.model.ScanHistoryEntry
import com.alphaai.app.ui.common.Format
import com.alphaai.app.ui.components.EmptyView
import com.alphaai.app.ui.components.LoadingView
import com.alphaai.app.ui.theme.AlphaColors

/** Verlaufs-Seite: die letzten Scans mit Zeitpunkt und Top-Chancen. */
@Composable
fun HistoryScreen(viewModel: HistoryViewModel) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    when {
        state.status.isLoading && state.entries.isEmpty() -> LoadingView()
        state.entries.isEmpty() ->
            EmptyView("Noch kein Verlauf. Öffne die Startseite, um den ersten Scan zu laden.")
        else ->
            LazyColumn(modifier = Modifier.fillMaxSize().testTag("history_list")) {
                items(state.entries, key = { it.timestamp }) { entry ->
                    HistoryCard(entry)
                }
            }
    }
}

@Composable
private fun HistoryCard(entry: ScanHistoryEntry) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp),
        colors = CardDefaults.cardColors(containerColor = AlphaColors.CarbonCard),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = Format.timestamp(entry.timestamp),
                style = MaterialTheme.typography.titleMedium,
                color = AlphaColors.TextPrimary,
                fontWeight = FontWeight.SemiBold,
            )
            Text(
                text = entry.session.ifBlank { "—" },
                color = AlphaColors.TextSecondary,
                modifier = Modifier.padding(top = 2.dp),
            )
            if (entry.topTickers.isNotEmpty()) {
                Text(
                    text = "Top: ${entry.topTickers.joinToString(" · ")}",
                    color = AlphaColors.Amber,
                    modifier = Modifier.padding(top = 8.dp),
                )
            }
        }
    }
}
