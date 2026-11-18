package app.morphe.patches.genv

import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.resourcePatch
import org.w3c.dom.Document
import org.w3c.dom.Element

private const val ANDROID_NS_ADS = "http://schemas.android.com/apk/res/android"
internal const val REMOVE_ADS_NAME = "Remove ads (experimental)"

private val adIdPermissions = setOf(
    "android.permission.ACCESS_ADSERVICES_AD_ID",
    "com.google.android.gms.permission.AD_ID",
)

private fun Element.androidName(): String =
    getAttributeNS(ANDROID_NS_ADS, "name").ifEmpty { getAttribute("android:name") }

/** Remove only reviewed AdMob configuration and advertising-ID access. */
internal fun removeAdvertisingManifestEntries(document: Document) {
    val root = document.documentElement
    require(root.tagName == "manifest" && root.getAttribute("package") == GENV_PACKAGE) {
        "Unexpected GenV manifest package"
    }
    val applications = root.getElementsByTagName("application")
    require(applications.length == 1) { "Unexpected GenV application element" }
    val application = applications.item(0) as Element

    val permissions = (0 until root.childNodes.length).mapNotNull { root.childNodes.item(it) as? Element }
        .filter { it.tagName == "uses-permission" && it.androidName() in adIdPermissions }
    require(permissions.size == adIdPermissions.size && permissions.map { it.androidName() }.toSet() == adIdPermissions) {
        "Reviewed GenV advertising-ID permissions changed"
    }

    val metadata = (0 until application.childNodes.length).mapNotNull { application.childNodes.item(it) as? Element }
        .filter { it.tagName == "meta-data" && it.androidName() == "com.google.android.gms.ads.APPLICATION_ID" }
    require(metadata.size == 1) { "Reviewed GenV AdMob application metadata changed" }

    permissions.forEach(root::removeChild)
    metadata.forEach(application::removeChild)
}

/**
 * Advertising-only manifest suppression. This deliberately leaves billing,
 * subscriptions, plan state, credits, purchases and server entitlements intact.
 */
@Suppress("unused")
val removeAdsPatch = resourcePatch(
    name = REMOVE_ADS_NAME,
    description = "Remove reviewed AdMob configuration and advertising-ID permissions from GenV 3.7.2; 3.7.4 support is provisional and fails closed if its manifest differs. Does not change premium status, billing, credits, rewards or server entitlements.",
    default = false,
) {
    compatibleWith(Compatibility(
        name = "GenV",
        packageName = GENV_PACKAGE,
        targets = GENV_TARGETS,
    ))
    execute {
        verifyGenVSource(packageMetadata)
        document("AndroidManifest.xml").use(::removeAdvertisingManifestEntries)
    }
}
