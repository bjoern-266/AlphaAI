package com.alphaai.app.domain.model

/** Zustand einer einzelnen Backend-Komponente (nur Anzeige). */
data class ComponentHealth(
    val name: String,
    val level: HealthLevel,
    val detail: String,
)

/** Aggregierter Gesundheitszustand des Backends. */
data class HealthReport(
    val level: HealthLevel,
    val components: List<ComponentHealth>,
    val uptimeSeconds: Int?,
    val version: String,
    val asOf: String?,
)

/** Statische Beschreibung des Backend-Dienstes (Version/Umgebung). */
data class ServiceInfo(
    val name: String,
    val version: String,
    val apiVersion: String,
    val environment: String,
    val uptimeSeconds: Int?,
)

/**
 * Ein Eintrag der Scan-Historie (Zeitpunkt + Top-Chancen des Scans).
 *
 * Wird aus den lokal gespeicherten Schnappschüssen aufgebaut.
 */
data class ScanHistoryEntry(
    val timestamp: String,
    val session: String,
    val scanCount: Int,
    val topTickers: List<String>,
)

/** Zustand des Discovery-/Scan-Prozesses für die Markets-Seite. */
data class DiscoveryStatus(
    val universeCount: Int?,
    val analyzedCount: Int?,
    val rejectedCount: Int?,
    val opportunityCount: Int,
    val markets: List<String>,
)
