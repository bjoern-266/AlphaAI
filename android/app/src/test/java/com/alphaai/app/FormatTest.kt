package com.alphaai.app

import com.alphaai.app.ui.common.Format
import org.junit.Assert.assertEquals
import org.junit.Test

/** Prüft die reine Anzeige-Formatierung (keine Fachlogik). */
class FormatTest {
    @Test
    fun `score formats integer or dash`() {
        assertEquals("82", Format.score(82.4))
        assertEquals("—", Format.score(null))
    }

    @Test
    fun `percent formats confidence`() {
        assertEquals("80 %", Format.percent(0.8))
        assertEquals("—", Format.percent(null))
    }

    @Test
    fun `countdown formats hours and minutes`() {
        assertEquals("1:00:00", Format.countdown(3600))
        assertEquals("5:00", Format.countdown(300))
        assertEquals("—", Format.countdown(null))
        assertEquals("—", Format.countdown(-1))
    }

    @Test
    fun `timestamp trims to minutes`() {
        assertEquals("2026-07-12 14:00", Format.timestamp("2026-07-12T14:00:00+00:00"))
        assertEquals("—", Format.timestamp(null))
    }
}
