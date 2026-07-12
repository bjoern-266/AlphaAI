package com.alphaai.app.ui.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.alphaai.app.domain.model.Opportunity
import com.alphaai.app.ui.common.Format
import com.alphaai.app.ui.theme.AlphaColors

/** Kleiner Kennzahlen-Chip (Label + Wert) für Karten. */
@Composable
fun StatChip(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = AlphaColors.TextMuted,
        )
        Text(
            text = value,
            style = MaterialTheme.typography.titleMedium,
            color = AlphaColors.TextPrimary,
            fontWeight = FontWeight.SemiBold,
        )
    }
}

/** Abschnittsüberschrift innerhalb einer Seite. */
@Composable
fun SectionHeader(
    title: String,
    modifier: Modifier = Modifier,
) {
    Text(
        text = title,
        style = MaterialTheme.typography.titleLarge,
        color = AlphaColors.TextPrimary,
        modifier = modifier.padding(horizontal = 16.dp, vertical = 8.dp),
    )
}

/**
 * Große Karte für eine Chance – Kern des Karten-Layouts.
 *
 * Zeigt ausschließlich vorhandene Werte an: Rang, Ticker, Richtung, Stärke,
 * Score, Confidence, Risk. Keine Kauf-/Verkaufsknöpfe.
 */
@Composable
fun OpportunityCard(
    opportunity: Opportunity,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(
        modifier =
            modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 6.dp)
                .testTag("opportunity_${opportunity.ticker}")
                .clickable(onClick = onClick),
        colors = CardDefaults.cardColors(containerColor = AlphaColors.CarbonCard),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    if (opportunity.rank > 0) {
                        Text(
                            text = "#${opportunity.rank}",
                            color = AlphaColors.Amber,
                            fontWeight = FontWeight.Bold,
                            style = MaterialTheme.typography.titleMedium,
                        )
                        Text(
                            text = "  ",
                            modifier = Modifier.width(8.dp),
                        )
                    }
                    Column {
                        Text(
                            text = opportunity.ticker,
                            style = MaterialTheme.typography.titleLarge,
                            color = AlphaColors.TextPrimary,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(
                            text = opportunity.company.ifBlank { opportunity.market },
                            style = MaterialTheme.typography.bodyMedium,
                            color = AlphaColors.TextSecondary,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                }
                DirectionBadge(opportunity.direction)
            }

            Row(
                modifier = Modifier.fillMaxWidth().padding(top = 14.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                StatChip("Score", Format.score(opportunity.opportunityScore))
                StatChip("Confidence", Format.percent(opportunity.confidence))
                StatChip("Risk", Format.risk(opportunity.risk))
                StrengthBadge(opportunity.strength)
            }

            if (opportunity.summary.isNotBlank()) {
                Text(
                    text = opportunity.summary,
                    style = MaterialTheme.typography.bodyMedium,
                    color = AlphaColors.TextSecondary,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.padding(top = 12.dp),
                )
            }
        }
    }
}
