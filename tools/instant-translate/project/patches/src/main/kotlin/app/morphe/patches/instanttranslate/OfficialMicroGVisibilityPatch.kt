package app.morphe.patches.instanttranslate

import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.resourcePatch
import org.w3c.dom.Document
import org.w3c.dom.Element

private const val ANDROID_NS = "http://schemas.android.com/apk/res/android"
private const val OFFICIAL_GMS_PACKAGE = "com.google.android.gms"

/** Adds only Android package visibility, never installs or impersonates a service. */
internal fun ensureOfficialMicroGVisibility(document: Document) {
    val root = document.documentElement
    require(root.tagName == "manifest" && root.getAttribute("package") == "com.spaceship.screen.textcopy") {
        "Unexpected Android manifest package"
    }
    val queries = (root.getElementsByTagName("queries").item(0) as? Element)
        ?: document.createElement("queries").also { node ->
            val app = root.getElementsByTagName("application").item(0)
            root.insertBefore(node, app)
        }
    val packages = queries.getElementsByTagName("package")
    val exists = (0 until packages.length).any { index ->
        val entry = packages.item(index) as? Element
        entry?.getAttributeNS(ANDROID_NS, "name") == OFFICIAL_GMS_PACKAGE ||
            entry?.getAttribute("android:name") == OFFICIAL_GMS_PACKAGE
    }
    if (!exists) queries.appendChild(document.createElement("package").apply {
        setAttributeNS(ANDROID_NS, "android:name", OFFICIAL_GMS_PACKAGE)
    })
}

@Suppress("unused")
val officialMicroGVisibilityPatch = resourcePatch(
    name = "Official microG service visibility (experimental)",
    description = "Allow Android package discovery of the existing official microG/Play Services package com.google.android.gms. Requires separately installed official microG with compatible system signature spoofing. Does not install services, replace Google APIs, or guarantee account login. Device testing required.",
    default = false,
) {
    compatibleWith(Compatibility(
        name = "Instant Translate", packageName = "com.spaceship.screen.textcopy",
        targets = listOf(AppTarget(version = "v7.5.00307", minSdk = 29, isExperimental = true)),
    ))
    execute {
        document("AndroidManifest.xml").use(::ensureOfficialMicroGVisibility)
    }
}
