package com.alphaai.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import com.alphaai.app.ui.navigation.AlphaAiNavHost
import com.alphaai.app.ui.theme.AlphaAiTheme

/**
 * Einziger Einstiegspunkt der App. Setzt das Compose-UI und wählt das Theme
 * anhand der Benutzereinstellung. Enthält keine Fachlogik.
 */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val container = (application as AlphaAiApplication).container

        setContent {
            val settings by container.settingsRepository.settings.collectAsState(initial = null)
            val darkTheme = settings?.darkTheme ?: true
            AlphaAiTheme(darkTheme = darkTheme) {
                Surface(modifier = Modifier.fillMaxSize()) {
                    AlphaAiNavHost(container)
                }
            }
        }
    }
}
