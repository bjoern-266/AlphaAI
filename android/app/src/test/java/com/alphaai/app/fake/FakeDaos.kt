package com.alphaai.app.fake

import com.alphaai.app.data.local.OpportunityDao
import com.alphaai.app.data.local.OpportunityEntity
import com.alphaai.app.data.local.ScanHistoryDao
import com.alphaai.app.data.local.ScanHistoryEntity
import com.alphaai.app.data.local.SnapshotDao
import com.alphaai.app.data.local.SnapshotEntity

/** In-Memory-Ersatz für [OpportunityDao] (Cache-/Offline-Tests). */
class FakeOpportunityDao : OpportunityDao {
    private val store = linkedMapOf<String, OpportunityEntity>()

    override suspend fun upsertAll(items: List<OpportunityEntity>) {
        items.forEach { store[it.ticker] = it }
    }

    override suspend fun clear() = store.clear()

    override suspend fun all(): List<OpportunityEntity> = store.values.sortedBy { it.rank }

    override suspend fun byTicker(ticker: String): OpportunityEntity? = store[ticker]
}

/** In-Memory-Ersatz für [SnapshotDao]. */
class FakeSnapshotDao : SnapshotDao {
    private var snapshot: SnapshotEntity? = null

    override suspend fun upsert(snapshot: SnapshotEntity) {
        this.snapshot = snapshot
    }

    override suspend fun latest(): SnapshotEntity? = snapshot
}

/** In-Memory-Ersatz für [ScanHistoryDao]. */
class FakeScanHistoryDao : ScanHistoryDao {
    val store = linkedMapOf<String, ScanHistoryEntity>()

    override suspend fun upsert(entry: ScanHistoryEntity) {
        store[entry.timestamp] = entry
    }

    override suspend fun recent(limit: Int): List<ScanHistoryEntity> =
        store.values.sortedByDescending { it.cachedAt }.take(limit)

    override suspend fun trim(keep: Int) {
        val keepKeys =
            store.values.sortedByDescending { it.cachedAt }.take(keep).map { it.timestamp }.toSet()
        store.keys.retainAll(keepKeys)
    }
}
