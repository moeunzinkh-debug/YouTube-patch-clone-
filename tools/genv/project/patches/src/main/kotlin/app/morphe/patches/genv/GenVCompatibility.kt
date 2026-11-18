package app.morphe.patches.genv

import app.morphe.patcher.PackageMetadata
import app.morphe.patcher.patch.AppTarget

internal const val GENV_PACKAGE = "com.ainate.ai.video.generate"
internal val GENV_TARGETS = listOf(
    AppTarget(version = "3.7.2", minSdk = 24, isExperimental = true),
    // Provisional selector visibility requested for 3.7.4. The exact method,
    // manifest and signer guards in each patch still fail closed if it differs.
    AppTarget(version = "3.7.4", minSdk = 24, isExperimental = true),
)

internal fun requireSupportedGenVIdentity(metadata: PackageMetadata, selector: String) {
    val reviewed372 = metadata.versionName == "3.7.2" && metadata.versionCode == "163"
    val provisional374 = metadata.versionName == "3.7.4"
    require(metadata.packageName == GENV_PACKAGE && (reviewed372 || provisional374)) {
        "$selector supports reviewed GenV 3.7.2 (163) and provisional fail-closed GenV 3.7.4"
    }
}
