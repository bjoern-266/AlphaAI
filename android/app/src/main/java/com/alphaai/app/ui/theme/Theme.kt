package com.alphaai.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val DarkCarbonScheme =
    darkColorScheme(
        primary = AlphaColors.Amber,
        onPrimary = AlphaColors.OnAmber,
        secondary = AlphaColors.AmberDim,
        onSecondary = AlphaColors.OnAmber,
        background = AlphaColors.Carbon,
        onBackground = AlphaColors.TextPrimary,
        surface = AlphaColors.CarbonCard,
        onSurface = AlphaColors.TextPrimary,
        surfaceVariant = AlphaColors.CarbonElevated,
        onSurfaceVariant = AlphaColors.TextSecondary,
        outline = AlphaColors.CarbonBorder,
        error = AlphaColors.Short,
    )

// Fällt bewusst ebenfalls auf ein dunkles Schema zurück – AlphaAI ist dunkel.
private val LightFallbackScheme =
    lightColorScheme(
        primary = AlphaColors.AmberDim,
        onPrimary = AlphaColors.OnAmber,
        background = AlphaColors.Carbon,
        onBackground = AlphaColors.TextPrimary,
        surface = AlphaColors.CarbonCard,
        onSurface = AlphaColors.TextPrimary,
    )

/**
 * Wurzel-Theme der App (Material Design 3).
 *
 * @param darkTheme Ob das dunkle Carbon-Theme verwendet wird (Standard: an).
 * @param content Der zu umschließende Inhalt.
 */
@Composable
fun AlphaAiTheme(
    darkTheme: Boolean = isSystemInDarkTheme() || true,
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkCarbonScheme else LightFallbackScheme,
        typography = AlphaTypography,
        shapes = AlphaShapes,
        content = content,
    )
}
