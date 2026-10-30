import org.jetbrains.kotlin.gradle.dsl.JvmTarget

group = "app.morphe"
patches {
    about {
        name = "Instant Translate patches (experimental)"
        description = "An opt-in, version-scoped Google fallback for failed translation requests."
        source = "https://github.com/moeunzinkh-debug/YouTube-patch-clone-"
        author = "YouTube Patch Clone contributors"
        contact = "https://github.com/moeunzinkh-debug/YouTube-patch-clone-"
        website = "https://github.com/moeunzinkh-debug/YouTube-patch-clone-"
        license = "GNU General Public License v3.0"
    }
}
java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
    toolchain { languageVersion.set(JavaLanguageVersion.of(17)) }
}
kotlin { compilerOptions { jvmTarget.set(JvmTarget.JVM_17) } }
dependencies { testImplementation(kotlin("test-junit")) }
tasks.test { useJUnit() }
