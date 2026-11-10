package app.morphe.patches.simsimi

import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.resourcePatch

@Suppress("unused")
val adEligibilityPatch = resourcePatch(
    name = "Disable ad eligibility (experimental)",
    description = "Makes the SimSimi 9.2.3/9.2.6 canShowAds gate return false. Not a complete ad remover; does not grant rewards or membership. Device testing required."
) {
    compatibleWith(Compatibility(
        name = "SimSimi",
        packageName = "com.ismaker.android.simsimi",
        targets = listOf(
            AppTarget(version = "9.2.3", minSdk = 24, isExperimental = true),
            AppTarget(version = "9.2.6", minSdk = 24, isExperimental = true)
        )
    ))
    execute {
        val payload = get("assets/index.android.bundle")
        val patched = AdGateTransform.patch(payload.readBytes())
        payload.writeBytes(patched)
    }
}

/** Client-side gates only: no purchase, reward callback or server entitlement is forged. */
@Suppress("unused")
val membershipUiPatch = resourcePatch(
    name = "Unlock membership UI (client only, experimental)",
    description = "Enables local membership UI gates using a cloned membership status. Profile, cover, photo and conversation controls may still require server authorization. Does not grant server items, read receipts, billing or daily rewards."
) {
    compatibleWith(Compatibility(
        name = "SimSimi",
        packageName = "com.ismaker.android.simsimi",
        targets = listOf(
            AppTarget(version = "9.2.3", minSdk = 24, isExperimental = true),
            AppTarget(version = "9.2.6", minSdk = 24, isExperimental = true)
        )
    ))
    execute {
        val payload = get("assets/index.android.bundle")
        payload.writeBytes(AdGateTransform.patchMembership(payload.readBytes()))
    }
}

/** Selects the existing non-video flow; server authorization and reward responses stay intact. */
@Suppress("unused")
val dailyBonusPatch = resourcePatch(
    name = "Daily bonus without video (client path, experimental)",
    description = "SimSimi 9.2.3 only. Selects its existing membership non-video daily-bonus loader. The 9.2.6 flow changed to currentAdmobState, so a persisted Manager selection is safely ignored on 9.2.6 rather than failing or fabricating ad completion. Keeps server state, reward requests and errors unchanged; device testing required.",
    default = false
) {
    compatibleWith(Compatibility(
        name = "SimSimi", packageName = "com.ismaker.android.simsimi",
        targets = listOf(AppTarget(version = "9.2.3", minSdk = 24, isExperimental = true))
    ))
    execute {
        val payload = get("assets/index.android.bundle")
        payload.writeBytes(AdGateTransform.patchDailyBonus(payload.readBytes()))
    }
}
