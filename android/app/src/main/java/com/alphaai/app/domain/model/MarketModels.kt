package com.alphaai.app.domain.model

/** Zustand eines einzelnen Marktes (nur Anzeige). */
data class MarketState(
    val key: String,
    val title: String,
    val phase: String,
    val isOpen: Boolean,
    val nextPhase: String,
    val secondsToNext: Int?,
)

/** Zusammengefasster Zustand aller Märkte (Marktuhr). */
data class MarketClock(
    val asOf: String?,
    val currentSession: String,
    val markets: List<MarketState>,
    val openMarkets: List<String>,
    val nextOpenMarket: String,
    val nextOpenAt: String?,
)

/**
 * Kompakter Startbildschirm-Schnappschuss – bündelt alles für den ersten Blick.
 *
 * Wird aus dem Operations-Report des Backends abgeleitet (reine Übernahme).
 */
data class OperationSnapshot(
    val asOf: String?,
    val currentSession: String,
    val markets: List<MarketState>,
    val openMarkets: List<String>,
    val nextOpenMarket: String,
    val nextOpenAt: String?,
    val lastScanAt: String?,
    val nextScanAt: String?,
    val nextScanJob: String,
    val runningJob: String?,
    val scanCount: Int,
    val errorCount: Int,
    val health: HealthLevel,
    val heartbeatAlive: Boolean,
    val newOpportunities: List<String>,
    val newRisks: List<String>,
)
