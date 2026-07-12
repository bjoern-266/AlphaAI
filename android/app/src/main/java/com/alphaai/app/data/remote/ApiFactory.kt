package com.alphaai.app.data.remote

import com.alphaai.app.core.Constants
import kotlinx.serialization.json.Json
import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Response
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicReference

/**
 * Ersetzt zur Laufzeit den Host jeder Anfrage durch die konfigurierte
 * Backend-Adresse. So kann die Backend-Adresse in den Einstellungen geändert
 * werden, ohne Retrofit neu zu bauen.
 */
class HostSelectionInterceptor(defaultBaseUrl: String) : Interceptor {
    private val baseUrl = AtomicReference(defaultBaseUrl.toHttpUrlOrNull())

    /** Setzt die aktive Backend-Basisadresse (z. B. aus den Einstellungen). */
    fun setBaseUrl(url: String) {
        url.toHttpUrlOrNull()?.let { baseUrl.set(it) }
    }

    override fun intercept(chain: Interceptor.Chain): Response {
        val target: HttpUrl = baseUrl.get() ?: return chain.proceed(chain.request())
        val request = chain.request()
        val newUrl =
            request.url.newBuilder()
                .scheme(target.scheme)
                .host(target.host)
                .port(target.port)
                .build()
        return chain.proceed(request.newBuilder().url(newUrl).build())
    }
}

/** Baut den Retrofit-Client (kotlinx.serialization, konfigurierbarer Host). */
object ApiFactory {
    private val json =
        Json {
            ignoreUnknownKeys = true
            coerceInputValues = true
            isLenient = true
        }

    /**
     * Erzeugt eine [AlphaAiApi] mit dem übergebenen Host-Interceptor.
     *
     * @param hostInterceptor steuert die zur Laufzeit wählbare Backend-Adresse.
     * @param enableLogging aktiviert HTTP-Logging (nur für Debug-Zwecke).
     */
    fun create(
        hostInterceptor: HostSelectionInterceptor,
        enableLogging: Boolean = false,
    ): AlphaAiApi {
        val builder =
            OkHttpClient.Builder()
                .addInterceptor(hostInterceptor)
                .connectTimeout(Constants.NETWORK_TIMEOUT_SECONDS, TimeUnit.SECONDS)
                .readTimeout(Constants.NETWORK_TIMEOUT_SECONDS, TimeUnit.SECONDS)
        if (enableLogging) {
            builder.addInterceptor(
                HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BASIC },
            )
        }
        val contentType = "application/json".toMediaType()
        return Retrofit.Builder()
            // Platzhalter-Basis; der echte Host wird pro Anfrage gesetzt.
            .baseUrl("http://localhost/")
            .client(builder.build())
            .addConverterFactory(json.asConverterFactory(contentType))
            .build()
            .create(AlphaAiApi::class.java)
    }
}
