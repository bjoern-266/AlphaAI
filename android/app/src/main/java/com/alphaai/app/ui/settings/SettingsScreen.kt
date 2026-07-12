package com.alphaai.app.ui.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Divider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.alphaai.app.ui.components.LoadingView
import com.alphaai.app.ui.theme.AlphaColors

/** Einstellungs-Seite: Backend-Adresse, Auto-Refresh, Theme, Cache, Debug. */
@Composable
fun SettingsScreen(viewModel: SettingsViewModel) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val settings = state.settings ?: run {
        LoadingView()
        return
    }

    var backendField by remember(settings.backendUrl) { mutableStateOf(settings.backendUrl) }

    Column(
        modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
    ) {
        Text(
            text = "Einstellungen",
            style = MaterialTheme.typography.headlineMedium,
            color = AlphaColors.TextPrimary,
            fontWeight = FontWeight.Bold,
        )

        Text(
            text = "Backend-Adresse",
            style = MaterialTheme.typography.labelLarge,
            color = AlphaColors.TextSecondary,
            modifier = Modifier.padding(top = 20.dp, bottom = 6.dp),
        )
        OutlinedTextField(
            value = backendField,
            onValueChange = { backendField = it },
            singleLine = true,
            label = { Text("http://host:port/") },
            modifier = Modifier.fillMaxWidth().testTag("backend_field"),
        )
        Text(
            text = "Änderungen werden beim Verlassen des Feldes übernommen.",
            style = MaterialTheme.typography.labelSmall,
            color = AlphaColors.TextMuted,
            modifier = Modifier.padding(top = 4.dp),
        )
        androidx.compose.material3.TextButton(
            onClick = { viewModel.setBackendUrl(backendField) },
            modifier = Modifier.testTag("save_backend"),
        ) {
            Text("Speichern")
        }

        Divider(color = AlphaColors.CarbonBorder, modifier = Modifier.padding(vertical = 12.dp))

        SettingSwitch("Auto-Refresh", settings.autoRefresh, viewModel::setAutoRefresh, "auto_refresh")
        SettingSwitch("Dark Theme", settings.darkTheme, viewModel::setDarkTheme, "dark_theme")
        SettingSwitch(
            "Hintergrund-Refresh",
            settings.backgroundRefresh,
            viewModel::setBackgroundRefresh,
            "background_refresh",
        )
        SettingSwitch("Debug-Informationen", settings.debug, viewModel::setDebug, "debug")

        Divider(color = AlphaColors.CarbonBorder, modifier = Modifier.padding(vertical = 12.dp))

        Text("Cache", style = MaterialTheme.typography.titleMedium, color = AlphaColors.TextPrimary)
        Text(
            text =
                "Der lokale Room-Cache speichert ausschließlich den zuletzt erfolgreichen Scan " +
                    "für den Offline-Betrieb. Es findet keine Berechnung auf dem Gerät statt.",
            color = AlphaColors.TextSecondary,
            modifier = Modifier.padding(top = 6.dp),
        )

        if (settings.debug) {
            Text(
                text = "API: nur REST (Read-only). Keine Broker, keine Orders.",
                style = MaterialTheme.typography.labelSmall,
                color = AlphaColors.TextMuted,
                modifier = Modifier.padding(top = 12.dp),
            )
        }
    }
}

@Composable
private fun SettingSwitch(
    label: String,
    checked: Boolean,
    onChange: (Boolean) -> Unit,
    tag: String,
) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(label, color = AlphaColors.TextPrimary)
        Switch(
            checked = checked,
            onCheckedChange = onChange,
            modifier = Modifier.testTag("switch_$tag"),
        )
    }
}
