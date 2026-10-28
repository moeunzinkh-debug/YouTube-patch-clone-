package app.morphe.patches.simsimi

import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.resourcePatch

@Suppress("unused")
val adEligibilityPatch = resourcePatch(
    name = "Disable ad eligibility (experimental)",
    description = "Makes the exact SimSimi 9.2.3 canShowAds gate return false. Not a complete ad remover; does not grant rewards or membership. Device testing required."
) {
    compatibleWith(Compatibility(
        name = "SimSimi",
        packageName = "com.ismaker.android.simsimi",
        targets = listOf(AppTarget(version = "9.2.3", minSdk = 24, isExperimental = true))
    ))
    execute {
        val payload = get("assets/index.android.bundle")
        val patched = AdGateTransform.patch(payload.readBytes())
        payload.writeBytes(patched)
    }
}
