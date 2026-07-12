# AlphaAI – Release-Verschleierungsregeln.
# kotlinx.serialization: Serializer der @Serializable-Klassen behalten.
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.**
-keepclassmembers class **$$serializer { *; }
-keepclasseswithmembers class * { kotlinx.serialization.KSerializer serializer(...); }
-keep,includedescriptorclasses class com.alphaai.app.**$$serializer { *; }
-keepclassmembers class com.alphaai.app.data.remote.dto.** { *; }
# Retrofit
-keepattributes Signature, Exceptions
-keep,allowobfuscation interface com.alphaai.app.data.remote.AlphaAiApi
