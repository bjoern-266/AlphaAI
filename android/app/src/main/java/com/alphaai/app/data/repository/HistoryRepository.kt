package com.alphaai.app.data.repository

import com.alphaai.app.data.local.ScanHistoryDao
import com.alphaai.app.domain.model.ScanHistoryEntry

/** Liest die lokale Scan-Historie (aus den gespeicherten Schnappschüssen). */
class HistoryRepository(
    private val historyDao: ScanHistoryDao,
) {
    /** Gibt die letzten [limit] Historien-Einträge zurück (neueste zuerst). */
    suspend fun recent(limit: Int = 50): List<ScanHistoryEntry> =
        historyDao.recent(limit).map { entry ->
            ScanHistoryEntry(
                timestamp = entry.timestamp,
                session = entry.session,
                scanCount = entry.scanCount,
                topTickers = entry.topTickers,
            )
        }
}
