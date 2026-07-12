package com.alphaai.app.data.repository

import com.alphaai.app.core.AppResult
import com.alphaai.app.data.local.ScanHistoryDao
import com.alphaai.app.data.local.ScanHistoryEntity
import com.alphaai.app.data.local.SnapshotDao
import com.alphaai.app.data.mapper.toDomain
import com.alphaai.app.data.mapper.toEntity
import com.alphaai.app.data.mapper.toSnapshot
import com.alphaai.app.data.remote.AlphaAiApi
import com.alphaai.app.domain.model.HealthReport
import com.alphaai.app.domain.model.OperationSnapshot
import com.alphaai.app.domain.model.ServiceInfo

private const val HISTORY_KEEP = 50

/**
 * Liest den System-/Operations-Zustand aus der REST-API und pflegt den lokalen
 * Schnappschuss-Cache sowie die Scan-Historie (Offline-Betrieb).
 */
class SystemRepository(
    private val api: AlphaAiApi,
    private val snapshotDao: SnapshotDao,
    private val historyDao: ScanHistoryDao,
    private val topTickersProvider: suspend () -> List<String> = { emptyList() },
    private val now: () -> Long = System::currentTimeMillis,
) {
    /** Lädt den Startbildschirm-Schnappschuss (Operations-Report). */
    suspend fun snapshot(): AppResult<OperationSnapshot> =
        fetch(
            remote = { api.operations() },
            map = { it.toSnapshot() },
            onSuccess = { snapshot ->
                snapshotDao.upsert(snapshot.toEntity(now()))
                recordHistory(snapshot)
            },
            fallback = { snapshotDao.latest()?.toDomain() },
        )

    /** Lädt den aggregierten Health-Report. */
    suspend fun health(): AppResult<HealthReport> =
        fetch(remote = { api.health() }, map = { it.toDomain() })

    /** Lädt Version/Beschreibung des Dienstes. */
    suspend fun version(): AppResult<ServiceInfo> =
        fetch(remote = { api.version() }, map = { it.toDomain() })

    /** Gibt den zuletzt gespeicherten Schnappschuss zurück (Offline-Start). */
    suspend fun cachedSnapshot(): OperationSnapshot? = snapshotDao.latest()?.toDomain()

    private suspend fun recordHistory(snapshot: OperationSnapshot) {
        val timestamp = snapshot.lastScanAt ?: snapshot.asOf ?: return
        historyDao.upsert(
            ScanHistoryEntity(
                timestamp = timestamp,
                session = snapshot.currentSession,
                scanCount = snapshot.scanCount,
                topTickers = topTickersProvider(),
                cachedAt = now(),
            ),
        )
        historyDao.trim(HISTORY_KEEP)
    }
}
