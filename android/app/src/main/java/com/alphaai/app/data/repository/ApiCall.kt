package com.alphaai.app.data.repository

import com.alphaai.app.core.AppError
import com.alphaai.app.core.AppResult
import com.alphaai.app.data.remote.dto.EnvelopeDto
import retrofit2.HttpException
import java.io.IOException

/**
 * Führt einen API-Aufruf aus und übersetzt ihn in ein [AppResult].
 *
 * Ablauf (reine Auslieferung, keine Fachlogik):
 * 1. Erfolg mit Nutzlast → [AppResult.Success] (zuvor wird [onSuccess] gecacht),
 * 2. Antwort ohne Nutzlast/Fehlerhülle → [AppResult.Failure],
 * 3. Netzwerkfehler → [AppResult.Offline] mit dem letzten Cache-Stand (falls
 *    vorhanden), sonst [AppResult.Failure].
 */
internal suspend fun <T, D> fetch(
    remote: suspend () -> EnvelopeDto<T>,
    map: (T) -> D,
    onSuccess: suspend (D) -> Unit = {},
    fallback: suspend () -> D? = { null },
): AppResult<D> =
    try {
        val envelope = remote()
        val data = envelope.data
        if (envelope.ok && data != null) {
            val domain = map(data)
            onSuccess(domain)
            AppResult.Success(domain)
        } else {
            AppResult.Failure(
                AppError(
                    message = envelope.error?.message ?: "Unerwartete Antwort des Backends.",
                    code = envelope.error?.code ?: "invalid_response",
                    status = envelope.error?.status,
                ),
            )
        }
    } catch (io: IOException) {
        val cached = fallback()
        if (cached != null) {
            AppResult.Offline(cached, "Offline – letzter gespeicherter Stand (${io.messageOrType()}).")
        } else {
            AppResult.Failure(AppError("Keine Verbindung zum Backend.", "offline"))
        }
    } catch (http: HttpException) {
        AppResult.Failure(
            AppError(
                message = "Serverfehler (HTTP ${http.code()}).",
                code = "http_${http.code()}",
                status = http.code(),
            ),
        )
    }

private fun Throwable.messageOrType(): String = message ?: this::class.simpleName.orEmpty()
