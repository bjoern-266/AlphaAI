package com.alphaai.app

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.alphaai.app.domain.model.Direction
import com.alphaai.app.domain.model.Opportunity
import com.alphaai.app.domain.model.Strength
import com.alphaai.app.ui.components.OpportunityCard
import com.alphaai.app.ui.theme.AlphaAiTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

/** UI-Test der zentralen Chancen-Karte (Anzeige + Klick). */
class OpportunityCardTest {
    @get:Rule
    val composeRule = createComposeRule()

    private val sample =
        Opportunity(
            ticker = "AAPL",
            company = "Apple Inc.",
            market = "NASDAQ",
            sector = "Technology",
            direction = Direction.LONG,
            strength = Strength.HIGH,
            confidence = 0.8,
            opportunityScore = 82.0,
            risk = 70.0,
            rank = 1,
            summary = "Starker Aufwärtstrend",
        )

    @Test
    fun showsTickerAndScore() {
        composeRule.setContent {
            AlphaAiTheme { OpportunityCard(opportunity = sample, onClick = {}) }
        }
        composeRule.onNodeWithText("AAPL").assertIsDisplayed()
        composeRule.onNodeWithText("Apple Inc.").assertIsDisplayed()
        composeRule.onNodeWithText("82").assertIsDisplayed()
    }

    @Test
    fun clickInvokesCallback() {
        var clicked = 0
        composeRule.setContent {
            AlphaAiTheme { OpportunityCard(opportunity = sample, onClick = { clicked++ }) }
        }
        composeRule.onNodeWithText("AAPL").performClick()
        assertEquals(1, clicked)
    }
}
