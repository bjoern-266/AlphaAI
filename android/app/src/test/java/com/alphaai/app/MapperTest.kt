package com.alphaai.app

import com.alphaai.app.data.mapper.toDomain
import com.alphaai.app.data.mapper.toEntity
import com.alphaai.app.data.mapper.toSnapshot
import com.alphaai.app.data.remote.dto.OpportunityDto
import com.alphaai.app.domain.model.Direction
import com.alphaai.app.domain.model.HealthLevel
import com.alphaai.app.domain.model.Strength
import com.alphaai.app.fake.Fixtures
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Prüft die reinen Umwandlungen DTO ↔ Domäne ↔ Cache-Entity. */
class MapperTest {
    @Test
    fun `maps opportunity dto to domain`() {
        val domain = Fixtures.opportunity("AAPL", score = 82.0, direction = "long").toDomain()
        assertEquals("AAPL", domain.ticker)
        assertEquals(Direction.LONG, domain.direction)
        assertEquals(Strength.HIGH, domain.strength)
        assertEquals(82.0, domain.opportunityScore!!, 0.001)
        assertEquals(1, domain.rank)
    }

    @Test
    fun `uses discovery rank when opportunity rank missing`() {
        val dto = OpportunityDto(ticker = "NVDA", rank = 3, opportunityRank = 0)
        assertEquals(3, dto.toDomain().rank)
    }

    @Test
    fun `entity roundtrip preserves values`() {
        val original = Fixtures.opportunity("MSFT", score = 74.0).toDomain()
        val restored = original.toEntity(now = 1L).toDomain()
        assertEquals(original.ticker, restored.ticker)
        assertEquals(original.direction, restored.direction)
        assertEquals(original.strength, restored.strength)
        assertEquals(original.opportunityScore, restored.opportunityScore)
        assertEquals(original.reasons, restored.reasons)
    }

    @Test
    fun `maps operations report to snapshot`() {
        val snapshot = Fixtures.operations(session = "USA: open").toSnapshot()
        assertEquals("USA: open", snapshot.currentSession)
        assertEquals(2, snapshot.markets.size)
        assertEquals(listOf("us"), snapshot.openMarkets)
        assertEquals(HealthLevel.OK, snapshot.health)
        assertTrue(snapshot.heartbeatAlive)
        assertEquals(listOf("AAPL"), snapshot.newOpportunities)
    }

    @Test
    fun `unknown direction falls back to neutral`() {
        assertEquals(Direction.NEUTRAL, Direction.fromApi("sideways"))
        assertEquals(Strength.UNKNOWN, Strength.fromApi(null))
    }
}
