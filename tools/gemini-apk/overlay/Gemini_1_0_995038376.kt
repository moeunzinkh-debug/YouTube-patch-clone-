package app.morphe.patches.google.common.versions

import app.morphe.patches.google.common.AppVersionProfile
import app.morphe.patches.google.common.HookId
import app.morphe.patches.google.common.TargetSpec

val gemini10995038376 = AppVersionProfile(
    appName = "Gemini launcher",
    packageName = "com.google.android.apps.bard",
    versionName = "1.0.995038376",
    versionCode = "345",
    inputSha256 = mapOf("gemini-base.apk" to "bfa9b10060a1c0e8a1c3f2b01cd513f74a53b364ab9bdb1bca02ae103de3f7e5"),
    validation = listOf("2026-10-27: inspected user-supplied APK code 345; four exact-package DEX references; device validation pending"),
    hooks = mapOf(
        HookId.GEMINI_TARGET_REDIRECT to TargetSpec(
            anchorStrings = listOf("com.google.android.googlequicksearchbox"),
            expectedMatches = 4,
            description = "Replace four exact-package string references with the cloned Google package."
        ),
        HookId.SPLIT_RESTRICTION_REMOVAL to TargetSpec(description = "Remove requiredSplitTypes, splitTypes and vending.splits metadata."),
        HookId.APP_LABEL_UPDATE to TargetSpec(description = "Gemini (Morphe)")
    )
)
