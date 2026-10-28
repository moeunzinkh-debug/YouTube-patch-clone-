package app.morphe.patches.simsimi

import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.resourcePatch

private fun featureGate(name: String, key: String, detail: String) = resourcePatch(
    name = name,
    description = "$detail Client gates only; server authorization/data can still restrict the feature. Device testing required.",
    default = false
) {
    compatibleWith(Compatibility(
        name = "SimSimi", packageName = "com.ismaker.android.simsimi",
        targets = listOf(AppTarget(version = "9.2.3", minSdk = 24, isExperimental = true))
    ))
    dependsOn(membershipUiPatch)
    execute {
        val payload = get("assets/index.android.bundle")
        payload.writeBytes(AdGateTransform.patchFeature(payload.readBytes(), key))
    }
}

@Suppress("unused")
val conversationLevelPatch = featureGate(
    "Conversation level controls (client only, experimental)", "conversation_level",
    "Allows the membership branch of the conversation-level slider; retains original level range, topic safety controls and server save request."
)
@Suppress("unused")
val profilePhotoPatch = featureGate(
    "Profile photo controls (client only, experimental)", "profile_photo",
    "Opens the existing profile-photo picker rather than the membership upsell. Original image upload and server errors remain intact."
)
@Suppress("unused")
val groupCoverPatch = featureGate(
    "Custom group cover controls (client only, experimental)", "group_cover",
    "Opens the custom-cover picker and preserves the custom selection on submission. Does not grant group ownership or server upload rights."
)
@Suppress("unused")
val photoSendPatch = featureGate(
    "Photo sending controls (client only, experimental)", "photo_send",
    "Enables membership controls in direct/group photo composers. Does not fake sends, reset quotas, remove moderation or override server upload limits."
)
@Suppress("unused")
val readReceiptsPatch = featureGate(
    "Read receipt display (client only, experimental)", "read_receipts",
    "Removes the membership question-mark cover over the existing receipt display. Preserves the real msgHasBeenRead flag; never fabricates a read receipt."
)
@Suppress("unused")
val itemControlsPatch = featureGate(
    "Membership item controls (client only, experimental)", "item_controls",
    "Enables membership UI controls in both item modal paths. Does NOT grant all items, unlimited stock, coins or successful server item use."
)
