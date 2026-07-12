package com.alphaai.app

import com.alphaai.app.data.remote.dto.EnvelopeDto
import com.alphaai.app.data.remote.dto.OpportunityReportDto
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Prüft, dass die einheitliche API-Hülle (Envelope) korrekt geparst wird. */
class EnvelopeSerializationTest {
    private val json = Json { ignoreUnknownKeys = true; coerceInputValues = true }

    @Test
    fun `parses success envelope with opportunity report`() {
        val body =
            """
            {"ok":true,"data":{"opportunities":[
              {"ticker":"AAPL","company":"Apple","market":"NASDAQ","sector":"Tech",
               "direction":"long","recommendation_strength":"high","confidence":0.8,
               "opportunity_score":82.0,"risk":70.0,"opportunity_rank":1,"summary":"stark"}
            ]},"error":null,"meta":{"api_version":"v1","kind":"opportunities"}}
            """.trimIndent()
        val envelope: EnvelopeDto<OpportunityReportDto> = json.decodeFromString(body)

        assertTrue(envelope.ok)
        assertEquals("v1", envelope.meta["api_version"])
        val opportunity = envelope.data!!.opportunities.single()
        assertEquals("AAPL", opportunity.ticker)
        assertEquals(82.0, opportunity.opportunityScore!!, 0.001)
        assertEquals("high", opportunity.recommendationStrength)
    }

    @Test
    fun `parses error envelope`() {
        val body =
            """
            {"ok":false,"data":null,
             "error":{"status":404,"code":"not_found","message":"nicht gefunden"},
             "meta":{"api_version":"v1"}}
            """.trimIndent()
        val envelope: EnvelopeDto<OpportunityReportDto> = json.decodeFromString(body)

        assertFalse(envelope.ok)
        assertEquals(404, envelope.error!!.status)
        assertEquals("not_found", envelope.error!!.code)
    }

    @Test
    fun `ignores unknown fields`() {
        val body = """{"ok":true,"data":{"opportunities":[],"unknown_field":42},"future":"x"}"""
        val envelope: EnvelopeDto<OpportunityReportDto> = json.decodeFromString(body)
        assertTrue(envelope.ok)
        assertTrue(envelope.data!!.opportunities.isEmpty())
    }
}
