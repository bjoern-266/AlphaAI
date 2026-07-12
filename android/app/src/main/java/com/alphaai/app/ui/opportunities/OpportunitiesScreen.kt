package com.alphaai.app.ui.opportunities

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.alphaai.app.domain.model.Direction
import com.alphaai.app.ui.components.EmptyView
import com.alphaai.app.ui.components.ErrorView
import com.alphaai.app.ui.components.LoadingView
import com.alphaai.app.ui.components.OfflineBanner
import com.alphaai.app.ui.components.OpportunityCard

/** Chancen-Seite mit Suche, Richtungsfilter und Sortierung. */
@Composable
fun OpportunitiesScreen(
    viewModel: OpportunitiesViewModel,
    onOpportunityClick: (String) -> Unit,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    when {
        state.status.isLoading && state.all.isEmpty() -> LoadingView()
        state.status.hasError && state.all.isEmpty() ->
            ErrorView(state.status.errorMessage.orEmpty(), viewModel::refresh)
        else -> {
            Column(modifier = Modifier.fillMaxSize()) {
                state.status.offlineReason?.let { OfflineBanner(it) }
                FilterBar(
                    filter = state.filter,
                    onQuery = viewModel::setQuery,
                    onDirection = viewModel::setDirection,
                    onSort = viewModel::setSort,
                )
                if (state.visible.isEmpty()) {
                    EmptyView("Keine Chancen für die aktuelle Auswahl.")
                } else {
                    LazyColumn(modifier = Modifier.fillMaxSize().testTag("opportunities_list")) {
                        items(state.visible, key = { it.ticker }) { opportunity ->
                            OpportunityCard(
                                opportunity = opportunity,
                                onClick = { onOpportunityClick(opportunity.ticker) },
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun FilterBar(
    filter: OpportunityFilter,
    onQuery: (String) -> Unit,
    onDirection: (Direction?) -> Unit,
    onSort: (SortMode) -> Unit,
) {
    Column(modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp)) {
        OutlinedTextField(
            value = filter.query,
            onValueChange = onQuery,
            label = { Text("Ticker oder Unternehmen suchen") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth().testTag("search_field"),
        )

        Text(
            text = "Richtung",
            style = MaterialTheme.typography.labelLarge,
            modifier = Modifier.padding(top = 12.dp, bottom = 4.dp),
        )
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            DirectionChip("Alle", filter.direction == null) { onDirection(null) }
            DirectionChip("Long", filter.direction == Direction.LONG) { onDirection(Direction.LONG) }
            DirectionChip("Short", filter.direction == Direction.SHORT) { onDirection(Direction.SHORT) }
        }

        Text(
            text = "Sortierung",
            style = MaterialTheme.typography.labelLarge,
            modifier = Modifier.padding(top = 12.dp, bottom = 4.dp),
        )
        Row(
            modifier = Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            SortMode.entries.forEach { mode ->
                DirectionChip(mode.label, filter.sort == mode) { onSort(mode) }
            }
        }
    }
}

@Composable
private fun DirectionChip(
    label: String,
    selected: Boolean,
    onClick: () -> Unit,
) {
    FilterChip(
        selected = selected,
        onClick = onClick,
        label = { Text(label) },
        modifier = Modifier.testTag("chip_$label"),
    )
}
