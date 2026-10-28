import org.jetbrains.kotlin.gradle.dsl.JvmTarget

group = "app.morphe"
patches {
    about {
        name = "SimSimi patches (experimental)"
        description = "Separate exact-build SimSimi experiments. No claim of server entitlement unlocks."
        source = "https://github.com/moeunzinkh-debug/YouTube-patch-clone-"
        author = "YouTube Patch Clone contributors"
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
