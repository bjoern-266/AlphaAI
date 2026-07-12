package com.alphaai.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.layout.padding
import com.alphaai.app.domain.model.Direction
import com.alphaai.app.domain.model.HealthLevel
import com.alphaai.app.domain.model.Strength
import com.alphaai.app.ui.theme.AlphaColors

/** Farbige Plakette für die Handelsrichtung (nur Anzeige, keine Order). */
@Composable
fun DirectionBadge(direction: Direction) {
    val color =
        when (direction) {
            Direction.LONG -> AlphaColors.Long
            Direction.SHORT -> AlphaColors.Short
            Direction.NEUTRAL -> AlphaColors.Neutral
        }
    Pill(text = direction.label, color = color)
}

/** Plakette für die Empfehlungsstärke. */
@Composable
fun StrengthBadge(strength: Strength) {
    val color =
        when (strength) {
            Strength.VERY_HIGH, Strength.HIGH -> AlphaColors.Amber
            Strength.MEDIUM -> AlphaColors.Warning
            else -> AlphaColors.Neutral
        }
    Pill(text = strength.label, color = color)
}

/** Kleiner farbiger Punkt/Chip für einen Gesundheitszustand. */
@Composable
fun HealthBadge(level: HealthLevel) {
    val color =
        when (level) {
            HealthLevel.OK -> AlphaColors.HealthOk
            HealthLevel.DEGRADED -> AlphaColors.HealthDegraded
            HealthLevel.ERROR -> AlphaColors.HealthError
            HealthLevel.UNKNOWN -> AlphaColors.HealthUnknown
        }
    Pill(text = level.label, color = color)
}

/** Wiederverwendbare Plakette mit farbigem, transparentem Hintergrund. */
@Composable
fun Pill(
    text: String,
    color: Color,
    modifier: Modifier = Modifier,
) {
    Text(
        text = text,
        color = color,
        fontWeight = FontWeight.SemiBold,
        modifier =
            modifier
                .clip(RoundedCornerShape(999.dp))
                .background(color.copy(alpha = 0.16f))
                .padding(PaddingValues(horizontal = 10.dp, vertical = 4.dp)),
    )
}
