plugins {
    java
}

// Compile the actual HTTP client, not a copy or an Android mock. Test dependencies
// live only here and are never included in the YouTube extension or patch bundle.
sourceSets {
    main {
        java.setSrcDirs(listOf("../extensions/youtube/src/main/java"))
        java.include("app/morphe/extension/youtube/patches/voiceovertranslation/KhmerTtsClient.java")
    }
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

dependencies {
    implementation("org.json:json:20240303")
    testImplementation("junit:junit:4.13.2")
}

tasks.test {
    useJUnit()
    testLogging {
        events("passed", "failed", "skipped")
        exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
    }
}
