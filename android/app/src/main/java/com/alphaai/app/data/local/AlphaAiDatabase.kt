package com.alphaai.app.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverter
import androidx.room.TypeConverters

/** Wandelt Listen von Zeichenketten für Room um (Unit-Separator-getrennt). */
class Converters {
    @TypeConverter
    fun fromStringList(value: List<String>): String = value.joinToString(SEPARATOR)

    @TypeConverter
    fun toStringList(value: String): List<String> =
        if (value.isEmpty()) emptyList() else value.split(SEPARATOR)

    private companion object {
        // Unit-Separator (U+001F): kommt in Tickern/Texten praktisch nie vor.
        const val SEPARATOR = "\u001F"
    }
}

/** Lokale Room-Datenbank – **ausschließlich** Cache für den Offline-Betrieb. */
@Database(
    entities = [OpportunityEntity::class, SnapshotEntity::class, ScanHistoryEntity::class],
    version = 1,
    exportSchema = false,
)
@TypeConverters(Converters::class)
abstract class AlphaAiDatabase : RoomDatabase() {
    abstract fun opportunityDao(): OpportunityDao

    abstract fun snapshotDao(): SnapshotDao

    abstract fun scanHistoryDao(): ScanHistoryDao

    companion object {
        const val NAME = "alphaai_cache.db"
    }
}
