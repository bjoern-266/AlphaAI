package com.alphaai.app.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Aggregierter Health-Report (`/health`). */
@Serializable
data class HealthDto(
    val status: String = "unknown",
    val components: List<ComponentDto> = emptyList(),
    @SerialName("uptime_seconds") val uptimeSeconds: Int? = null,
    val version: String = "",
    @SerialName("as_of") val asOf: String? = null,
)

/** Zustand einer einzelnen Komponente. */
@Serializable
data class ComponentDto(
    val name: String = "",
    val status: String = "unknown",
    val detail: String = "",
)

/** Version/Beschreibung des Dienstes (`/version`). */
@Serializable
data class ServiceInfoDto(
    val name: String = "",
    val version: String = "",
    @SerialName("api_version") val apiVersion: String = "",
    val environment: String = "",
    @SerialName("uptime_seconds") val uptimeSeconds: Int? = null,
)
