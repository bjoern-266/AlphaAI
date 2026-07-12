package com.alphaai.app.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

/** Zugriff auf zwischengespeicherte Chancen. */
@Dao
interface OpportunityDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(items: List<OpportunityEntity>)

    @Query("DELETE FROM opportunities")
    suspend fun clear()

    @Query("SELECT * FROM opportunities ORDER BY rank ASC")
    suspend fun all(): List<OpportunityEntity>

    @Query("SELECT * FROM opportunities WHERE ticker = :ticker LIMIT 1")
    suspend fun byTicker(ticker: String): OpportunityEntity?

    /** Ersetzt den gesamten Cache atomar (löschen + einfügen). */
    suspend fun replaceAll(items: List<OpportunityEntity>) {
        clear()
        upsertAll(items)
    }
}

/** Zugriff auf den einzeiligen Startbildschirm-Schnappschuss. */
@Dao
interface SnapshotDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(snapshot: SnapshotEntity)

    @Query("SELECT * FROM snapshot WHERE id = 0 LIMIT 1")
    suspend fun latest(): SnapshotEntity?
}

/** Zugriff auf die lokale Scan-Historie. */
@Dao
interface ScanHistoryDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entry: ScanHistoryEntity)

    @Query("SELECT * FROM scan_history ORDER BY cachedAt DESC LIMIT :limit")
    suspend fun recent(limit: Int): List<ScanHistoryEntity>

    @Query(
        "DELETE FROM scan_history WHERE timestamp NOT IN " +
            "(SELECT timestamp FROM scan_history ORDER BY cachedAt DESC LIMIT :keep)",
    )
    suspend fun trim(keep: Int)
}
