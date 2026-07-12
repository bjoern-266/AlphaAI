package com.alphaai.app.data.repository

import com.alphaai.app.core.AppError
import com.alphaai.app.core.AppResult
import com.alphaai.app.data.local.OpportunityDao
import com.alphaai.app.data.mapper.toDomain
import com.alphaai.app.data.mapper.toEntity
import com.alphaai.app.data.remote.AlphaAiApi
import com.alphaai.app.domain.model.Opportunity

/**
 * Liest Chancen ausschließlich aus der REST-API und spiegelt sie in den lokalen
 * Room-Cache (für den Offline-Betrieb). Es findet **keine** Berechnung statt.
 */
class OpportunityRepository(
    private val api: AlphaAiApi,
    private val dao: OpportunityDao,
    private val now: () -> Long = System::currentTimeMillis,
) {
    /** Lädt alle Chancen (Opportunity-Report) und aktualisiert den Cache. */
    suspend fun opportunities(): AppResult<List<Opportunity>> =
        fetch(
            remote = { api.opportunities() },
            map = { report -> report.opportunities.map { it.toDomain() } },
            onSuccess = { list -> dao.replaceAll(list.map { it.toEntity(now()) }) },
            fallback = { cachedList() },
        )

    /** Lädt die Top-N-Chancen (nach Ranking). */
    suspend fun topOpportunities(limit: Int): AppResult<List<Opportunity>> =
        fetch(
            remote = { api.topOpportunities(limit) },
            map = { list -> list.map { it.toDomain() } },
            fallback = { cachedList().take(limit) },
        )

    /**
     * Lädt die Detailansicht einer Chance.
     *
     * Zuerst über den Opportunity-Endpunkt; ist der Ticker dort nicht vorhanden,
     * über den Empfehlungs-Endpunkt; andernfalls aus dem Cache (offline).
     */
    suspend fun detail(ticker: String): AppResult<Opportunity> {
        val primary =
            fetch(
                remote = { api.opportunity(ticker) },
                map = { it.toDomain() },
                onSuccess = { dao.upsertAll(listOf(it.toEntity(now()))) },
                fallback = { dao.byTicker(ticker)?.toDomain() },
            )
        if (primary !is AppResult.Failure) return primary

        val secondary =
            fetch(
                remote = { api.recommendation(ticker) },
                map = { it.toDomain() },
                fallback = { dao.byTicker(ticker)?.toDomain() },
            )
        if (secondary !is AppResult.Failure) return secondary

        val cached = dao.byTicker(ticker)?.toDomain()
        return if (cached != null) {
            AppResult.Offline(cached, "Offline – letzter gespeicherter Stand.")
        } else {
            AppResult.Failure(AppError("Keine Daten für '$ticker' verfügbar.", "not_found"))
        }
    }

    /** Gibt die zwischengespeicherten Chancen zurück (für Offline-Start). */
    suspend fun cached(): List<Opportunity> = cachedList()

    private suspend fun cachedList(): List<Opportunity> = dao.all().map { it.toDomain() }
}
