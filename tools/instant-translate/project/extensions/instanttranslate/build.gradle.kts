import com.android.build.api.dsl.ApplicationExtension

configure<ApplicationExtension> {
    namespace = "app.morphe.extension.instanttranslate"
    compileSdk = 36
    defaultConfig { minSdk = 29 }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20240303")
}
