package com.alphaai.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.alphaai.app.domain.model.MarketState
import com.alphaai.app.ui.common.Format
import com.alphaai.app.ui.theme.AlphaColors

/** Karte mit dem Zustand eines Marktes (offen/geschlossen, Phase, Countdown). */
@Composable
fun MarketStatusCard(
    market: MarketState,
    modifier: Modifier = Modifier,
) {
    Card(
        modifier = modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp),
        colors = CardDefaults.cardColors(containerColor = AlphaColors.CarbonCard),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier =
                        Modifier
                            .size(12.dp)
                            .clip(CircleShape)
                            .background(if (market.isOpen) AlphaColors.Long else AlphaColors.Neutral),
                )
                Column(modifier = Modifier.padding(start = 12.dp)) {
                    Text(
                        text = market.title.ifBlank { market.key },
                        style = MaterialTheme.typography.titleMedium,
                        color = AlphaColors.TextPrimary,
                        fontWeight = FontWeight.SemiBold,
                    )
                    Text(
                        text = if (market.isOpen) "Geöffnet · ${market.phase}" else "Geschlossen",
                        style = MaterialTheme.typography.bodyMedium,
                        color = AlphaColors.TextSecondary,
                    )
                }
            }
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = market.nextPhase.ifBlank { "—" },
                    style = MaterialTheme.typography.labelSmall,
                    color = AlphaColors.TextMuted,
                )
                Text(
                    text = Format.countdown(market.secondsToNext),
                    style = MaterialTheme.typography.titleMedium,
                    color = AlphaColors.Amber,
                    fontWeight = FontWeight.Bold,
                )
            }
        }
    }
}
