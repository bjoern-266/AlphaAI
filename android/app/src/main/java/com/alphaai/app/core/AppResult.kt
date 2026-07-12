package com.alphaai.app.core

/**
 * Ergebnis eines Datenzugriffs (Erfolg, Fehler oder Offline-Stand aus dem Cache).
 *
 * Der Client führt keine Geschäftslogik aus – dieser Typ transportiert nur den
 * Zustand eines API-/Cache-Zugriffs zur Anzeige.
 */
sealed interface AppResult<out T> {
    /** Erfolgreiche, frische Antwort vom Backend. */
    data class Success<T>(val data: T) : AppResult<T>

    /**
     * Offline-Stand: die Daten stammen aus dem lokalen Cache (kein frischer Scan).
     *
     * @param data die zuletzt erfolgreich gespeicherten Daten.
     * @param reason kurze Begründung (z. B. "Keine Verbindung").
     */
    data class Offline<T>(val data: T, val reason: String) : AppResult<T>

    /** Fehler ohne verwertbare Daten. */
    data class Failure(val error: AppError) : AppResult<Nothing>
}

/** Beschreibt einen fehlgeschlagenen Zugriff (nur Anzeige, keine Fachlogik). */
data class AppError(
    val message: String,
    val code: String = "error",
    val status: Int? = null,
)

/** Gibt die Daten bei Erfolg/Offline zurück (oder null bei Fehler). */
fun <T> AppResult<T>.dataOrNull(): T? =
    when (this) {
        is AppResult.Success -> data
        is AppResult.Offline -> data
        is AppResult.Failure -> null
    }
