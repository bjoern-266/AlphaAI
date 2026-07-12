package com.alphaai.app.data.remote.dto

import kotlinx.serialization.Serializable

/**
 * Einheitliche Antwort-Hülle des Backends (siehe `docs/API.md`).
 *
 * Jede API-Antwort hat dieselbe äußere Struktur. Der generische Typ [T] ist die
 * jeweilige Nutzlast (z. B. ein Report-DTO).
 */
@Serializable
data class EnvelopeDto<T>(
    val ok: Boolean = false,
    val data: T? = null,
    val error: ApiErrorDto? = null,
    val meta: Map<String, String> = emptyMap(),
)

/** Strukturierte Fehlerinformation einer API-Antwort. */
@Serializable
data class ApiErrorDto(
    val status: Int = 0,
    val code: String = "error",
    val message: String = "",
)
