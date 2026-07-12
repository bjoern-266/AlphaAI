package com.alphaai.app

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.navigation.compose.rememberNavController
import com.alphaai.app.ui.navigation.BottomNavBar
import com.alphaai.app.ui.theme.AlphaAiTheme
import org.junit.Rule
import org.junit.Test

/** UI-Test der unteren Navigationsleiste (alle fünf Bereiche sichtbar). */
class BottomNavBarTest {
    @get:Rule
    val composeRule = createComposeRule()

    @Test
    fun showsAllTabs() {
        composeRule.setContent {
            AlphaAiTheme {
                val navController = rememberNavController()
                BottomNavBar(navController)
            }
        }
        listOf("Home", "Chancen", "Märkte", "Verlauf", "Einstellungen").forEach { label ->
            composeRule.onNodeWithText(label).assertIsDisplayed()
        }
    }
}
