package com.alphaai.app

import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/**
 * Statische Architektur-Prüfung (analog zum Backend-`quality_check`).
 *
 * Erzwingt die Schichtung per Import-Analyse, ohne die Module zu laden:
 * - `ui` darf nicht direkt auf `data.remote`/`data.local` zugreifen (nur über
 *   Repositories/Domäne),
 * - `domain` darf nichts aus `data`, `ui`, Android, Retrofit oder Room importieren,
 * - `data.mapper`/`data.repository` bleiben frei von `ui`.
 */
class ArchitectureTest {
    private val sourceRoot = File("src/main/java/com/alphaai/app")

    private data class Rule(val pathPart: String, val forbidden: List<String>)

    private val rules =
        listOf(
            Rule(
                pathPart = "/ui/",
                forbidden = listOf("com.alphaai.app.data.remote", "com.alphaai.app.data.local"),
            ),
            Rule(
                pathPart = "/domain/",
                forbidden =
                    listOf(
                        "com.alphaai.app.data",
                        "com.alphaai.app.ui",
                        "android.",
                        "retrofit2",
                        "androidx.room",
                    ),
            ),
            Rule(pathPart = "/data/", forbidden = listOf("com.alphaai.app.ui")),
        )

    @Test
    fun `layering rules are respected`() {
        assertTrue("Quellverzeichnis nicht gefunden: ${sourceRoot.absolutePath}", sourceRoot.isDirectory)
        val violations = mutableListOf<String>()

        sourceRoot.walkTopDown().filter { it.extension == "kt" }.forEach { file ->
            val normalizedPath = file.path.replace('\\', '/')
            val imports = file.readLines().filter { it.trimStart().startsWith("import ") }
            rules.forEach { rule ->
                if (normalizedPath.contains(rule.pathPart)) {
                    rule.forbidden.forEach { forbidden ->
                        if (imports.any { it.contains(forbidden) }) {
                            violations += "${file.name}: verbotener Import '$forbidden'"
                        }
                    }
                }
            }
        }

        assertTrue("Architektur-Verstöße:\n${violations.joinToString("\n")}", violations.isEmpty())
    }

    @Test
    fun `no trading actions in source`() {
        val forbiddenSymbols = listOf("placeOrder", "submitOrder", "executeTrade", "brokerApi")
        val hits = mutableListOf<String>()
        sourceRoot.walkTopDown().filter { it.extension == "kt" }.forEach { file ->
            val text = file.readText()
            forbiddenSymbols.forEach { symbol ->
                if (text.contains(symbol)) hits += "${file.name}: '$symbol'"
            }
        }
        assertTrue("Verbotene Handels-Aktionen gefunden:\n${hits.joinToString("\n")}", hits.isEmpty())
    }
}
