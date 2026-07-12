package com.alphaai.app.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Zwischengespeicherte Chance (nur lokaler Cache für den Offline-Betrieb).
 *
 * Der Cache ist ausschließlich eine Kopie des zuletzt erfolgreich geladenen
 * Backend-Stands – es findet **keine** Berechnung statt.
 */
@Entity(tableName = "opportunities")
data class OpportunityEntity(
    @PrimaryKey val ticker: String,
    val company: String,
    val market: String,
    val sector: String,
    val direction: String,
    val strength: String,
    val confidence: Double?,
    val opportunityScore: Double?,
    val risk: Double?,
    val rank: Int,
    val summary: String,
    val reasons: List<String>,
    val warnings: List<String>,
    val patternSummary: String,
    val strategySummary: String,
    val analyticsSummary: String,
    val backtestSummary: String,
    val paperTradingSummary: String,
    val analyzedAt: String?,
    val cachedAt: Long,
)

/** Einzeiliger Schnappschuss des Startbildschirms (Operations-Report-Auszug). */
@Entity(tableName = "snapshot")
data class SnapshotEntity(
    @PrimaryKey val id: Int = 0,
    val asOf: String?,
    val currentSession: String,
    val marketsJson: String,
    val openMarkets: List<String>,
    val nextOpenMarket: String,
    val nextOpenAt: String?,
    val lastScanAt: String?,
    val nextScanAt: String?,
    val nextScanJob: String,
    val runningJob: String?,
    val scanCount: Int,
    val errorCount: Int,
    val health: String,
    val heartbeatAlive: Boolean,
    val newOpportunities: List<String>,
    val newRisks: List<String>,
    val cachedAt: Long,
)

/** Ein Eintrag der lokalen Scan-Historie (Zeitpunkt + Top-Chancen). */
@Entity(tableName = "scan_history")
data class ScanHistoryEntity(
    @PrimaryKey val timestamp: String,
    val session: String,
    val scanCount: Int,
    val topTickers: List<String>,
    val cachedAt: Long,
)
