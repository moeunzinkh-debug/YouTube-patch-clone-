package app.morphe.patches.google.common.versions

import app.morphe.patches.google.common.AppVersionProfile
import app.morphe.patches.google.common.HookId
import app.morphe.patches.google.common.TargetSpec

/** Verified against these exact inputs. Retain this file when adding another version. */
val google17659 = AppVersionProfile(
    appName = "Google App (AGSA)",
    packageName = "com.google.android.googlequicksearchbox",
    versionName = "17.6.59.ve.arm64",
    versionCode = "301698282",
    inputSha256 = mapOf("google-base.apk" to "f9e5d898a8bae360e6d8654f1871b920e1a2774701fe716f4e64bb0c803b7bd9"),
    validation = listOf("2026-10-27: exact APK DEX discovery; patch execution and runtime validation tracked separately"),
    hooks = mapOf(
        HookId.WORK_PROFILE_BYPASS to TargetSpec(
            className = "Laezk;", methodName = "f",
            methodDescriptor = "(Leksz;Lfkya;)Ljava/lang/Object;",
            anchorStrings = listOf(
                "Trampolining to web app for work profile. %s",
                "Skipping trampoline to web app for work profile."
            ),
            expectedMatches = 2,
            integers = mapOf("lookback" to 60, "observedRegisters" to 46),
            description = "Both fingerprints resolve the same method; preserve the existing two insertions. Old Lauby.a record was incorrect."
        ),
        HookId.WORK_PROFILE_ELIGIBILITY to TargetSpec(
            className = "Lakpt;", methodName = "k",
            methodDescriptor = "(Lfkya;)Ljava/lang/Object;",
            fieldName = "x", fieldType = "Z",
            anchorStrings = listOf(
                "Robin eligibility : is disallowed on Work profile",
                "Robin eligibility : Work profile is allowed."
            ),
            expectedMatches = 1,
            integers = mapOf("errorCode" to 19),
            description = "Replace IGET_BOOLEAN with same-width const/16 true; retain other eligibility checks."
        ),
        HookId.MICROG_RUNTIME_PERMISSIONS to TargetSpec(
            className = "Lcom/google/android/apps/search/assistant/surfaces/voice/robin/main/MainActivity;",
            methodName = "onCreate", methodDescriptor = "(Landroid/os/Bundle;)V",
            fieldName = "o", fieldType = "Z", expectedMatches = 1,
            integers = mapOf(
                "minRegisters" to 11, "maxRegisters" to 17, "observedRegisters" to 12,
                "thisParameterOffset" to 2, "scratchArray" to 6, "scratchIndex" to 7, "scratchString" to 8
            ),
            description = "Insert after final IPUT_BOOLEAN o:Z while p0 is Activity, before trace cleanup. Never insert at return."
        ),
        HookId.PROCESS_NAME_REDIRECT to TargetSpec(
            className = "Ldgtr;", methodName = "b", methodDescriptor = "()Ljava/lang/String;",
            anchorStrings = listOf("com.google.android.googlequicksearchbox:googleapp"),
            expectedMatches = 2,
            description = "Two provider return sites; strip .morphe only for the compiled Dagger process-name switch."
        ),
        HookId.MAIN_PROCESS_CHECK to TargetSpec(
            className = "Ldgtn;", methodName = "b", methodDescriptor = "()Z",
            anchorStrings = listOf("More than 1 custom main process specified"),
            expectedMatches = 1,
            description = "Anchor is in eact.a; patch provider call inside eact.b to Application.getProcessName."
        ),
        HookId.GMS_SIGNATURE_BYPASS to TargetSpec(
            className = "Lcdii;", methodName = "b", methodDescriptor = "(Landroid/content/Context;I)I",
            anchorStrings = listOf(
                " requires Google Play services, but their signature is invalid.",
                "The Google Play services resources were not found. Check your project configuration to ensure that the resources are included.",
                " requires Google Play services, but they are missing."
            ),
            expectedMatches = 1
        ),
        HookId.GMS_CERTIFICATE_VERIFIER to TargetSpec(
            className = "Lcdij;",
            anchorStrings = listOf("Unable to obtain package certificate history."),
            methodSignatures = listOf("b(Ljava/lang/String;)Z", "c(I)Z", "d(Landroid/content/pm/PackageInfo;Z)Z"),
            expectedMatches = 3
        ),
        HookId.GMS_CORE_REDIRECT to TargetSpec(
            anchorStrings = listOf("com.google.android.gms"),
            values = mapOf("originalGoogleSha1" to "38918a453d07199354f8b19af05ec6562ced5788"),
            description = "MicroG RE 7.3.0-dev.2 app.revanced.android.gms; retain Binder service actions, redirect UI actions. Shared mappings: GmsConstants.kt."
        ),
        HookId.PACKAGE_CLONE_REDIRECT to TargetSpec(
            anchorStrings = listOf("com.google.android.googlequicksearchbox"),
            description = "Exact-package redirect count is logged during real input patching; other enabled patches can affect count."
        ),
        HookId.SPLIT_RESTRICTION_REMOVAL to TargetSpec(description = "Remove manifest split requirements; resource split still needs package rename/signing."),
        HookId.APP_LABEL_UPDATE to TargetSpec(description = "Google (Morphe)"),
        HookId.ACCOUNT_SWITCH_LOCK_BYPASS to TargetSpec(
            enabled = false, anchorStrings = listOf("Acquired account-switch Mutex."),
            description = "Historical rejected approach. Do not enable; normal account synchronization is required."
        ),
        HookId.ACCOUNT_SYNC_LOOP_FIX to TargetSpec(
            enabled = false, anchorStrings = listOf("Binding to service"),
            description = "Historical rejected Binder-success spoof; caused hangs."
        ),
        HookId.ACCOUNT_CONVERT_FALLBACK to TargetSpec(
            enabled = false, className = "Lfyca;",
            anchorStrings = listOf("Found google email address as the old primary email address", "Failed to convert AGSA account name to account id."),
            description = "Historical unverified helper name. Fixed AccountId=1 broke token acquisition; never use for a new version."
        )
    )
)
