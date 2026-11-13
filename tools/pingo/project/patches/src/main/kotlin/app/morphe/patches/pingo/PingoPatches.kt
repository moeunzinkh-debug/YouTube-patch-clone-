package app.morphe.patches.pingo

import app.morphe.patcher.extensions.InstructionExtensions.addInstruction
import app.morphe.patcher.extensions.InstructionExtensions.addInstructions
import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.bytecodePatch
import com.android.tools.smali.dexlib2.AccessFlags
import com.android.tools.smali.dexlib2.Opcode
import com.android.tools.smali.dexlib2.iface.instruction.ReferenceInstruction
import com.android.tools.smali.dexlib2.iface.reference.MethodReference

private const val PAIRIP_APPLICATION = "Lcom/pairip/application/Application;"
private const val PAIRIP_CLIENT = "Lcom/pairip/licensecheck/LicenseClient;"
private const val PAIRIP_PROVIDER = "Lcom/pairip/licensecheck/LicenseContentProvider;"
private const val PAIRIP_RESPONSE = "Lcom/pairip/licensecheck/LicenseResponseHelper;"
private const val SUBSCRIPTION_STATUS = "Lcom/superwall/sdk/models/entitlements/SubscriptionStatus;"
private const val ACTIVE_STATUS = "Lcom/superwall/sdk/models/entitlements/SubscriptionStatus${'$'}Active;"
private const val ENTITLEMENT = "Lcom/superwall/sdk/models/entitlements/Entitlement;"

private fun compatibility() = Compatibility(
    name = "Pingo AI",
    packageName = "com.picoai.languageapp.android",
    targets = listOf(AppTarget(version = "5.4.8", minSdk = 26, isExperimental = true)),
)

private fun app.morphe.patcher.patch.BytecodePatchContext.requireExactPingo() {
    require(packageMetadata.versionName == "5.4.8" && packageMetadata.versionCode == "941") {
        "Pingo AI patches support only the reviewed 5.4.8 build 941 APK"
    }
}

@Suppress("unused")
val removeLicenseCheckPatch = bytecodePatch(
    name = "Remove license check",
    description = "Disables the two reviewed PairIP Play-license entry points in Pingo AI 5.4.8 (941). This is client-side only and does not grant purchases, subscriptions, credits, or server entitlements.",
    default = false,
) {
    compatibleWith(compatibility())
    execute {
        requireExactPingo()
        val application = mutableClassDefBy(PAIRIP_APPLICATION)
        val provider = mutableClassDefBy(PAIRIP_PROVIDER)
        val client = mutableClassDefBy(PAIRIP_CLIENT)
        fun refs(method: app.morphe.patcher.util.proxy.mutableTypes.MutableMethod) =
            requireNotNull(method.implementation).instructions
                .mapNotNull { (it as? ReferenceInstruction)?.reference as? MethodReference }
        fun callsCheck(method: app.morphe.patcher.util.proxy.mutableTypes.MutableMethod) = refs(method).any {
            it.definingClass == PAIRIP_CLIENT && it.name == "checkLicense" && it.returnType == "V" &&
                it.parameterTypes.map { p -> p.toString() } == listOf("Landroid/content/Context;")
        }
        val attach = application.methods.singleOrNull {
            it.name == "attachBaseContext" && it.returnType == "V" &&
                it.parameterTypes.map { p -> p.toString() } == listOf("Landroid/content/Context;")
        } ?: error("Reviewed PairIP application entry point changed")
        val providerCreate = provider.methods.singleOrNull {
            it.name == "onCreate" && it.returnType == "Z" && it.parameterTypes.isEmpty()
        } ?: error("Reviewed PairIP provider entry point changed")
        require(callsCheck(attach) && callsCheck(providerCreate)) { "Reviewed PairIP startup call sites changed" }

        val check = client.methods.singleOrNull {
            it.name == "checkLicense" && it.returnType == "V" &&
                it.parameterTypes.map { p -> p.toString() } == listOf("Landroid/content/Context;") &&
                AccessFlags.PUBLIC.isSet(it.accessFlags) && AccessFlags.STATIC.isSet(it.accessFlags)
        } ?: error("Reviewed PairIP checkLicense method changed")
        val initialize = client.methods.singleOrNull {
            it.name == "initializeLicenseCheck" && it.returnType == "V" && it.parameterTypes.isEmpty() &&
                AccessFlags.PUBLIC.isSet(it.accessFlags) && !AccessFlags.STATIC.isSet(it.accessFlags)
        } ?: error("Reviewed PairIP initializeLicenseCheck method changed")
        val checkBody = requireNotNull(check.implementation)
        val initBody = requireNotNull(initialize.implementation)
        val checkInstructions = checkBody.instructions.toList()
        val initInstructions = initBody.instructions.toList()
        require(checkBody.registerCount == 3 && checkInstructions.size == 16 &&
            checkInstructions.first().opcode == Opcode.CONST_STRING &&
            refs(check).any { it.definingClass == PAIRIP_CLIENT && it.name == "isIsolatedProcess" }
        ) { "PairIP checkLicense layout changed or is already patched" }
        require(initBody.registerCount == 4 && initInstructions.size == 29 &&
            initInstructions.first().opcode == Opcode.SGET_OBJECT &&
            refs(initialize).any { it.definingClass == PAIRIP_RESPONSE && it.name == "validateResponse" } &&
            refs(initialize).any { it.definingClass == PAIRIP_CLIENT && it.name == "initiateFreshLicensingServiceConnection" }
        ) { "PairIP initialization layout changed or is already patched" }
        check.addInstruction(0, "return-void")
        initialize.addInstruction(0, "return-void")
    }
}

@Suppress("unused")
val unlockAllFeaturePatch = bytecodePatch(
    name = "Unlock all feature",
    description = "Forces the reviewed Superwall local SubscriptionStatus and Entitlement active predicates to true. This may suppress local paywall gates, but cannot create purchases, credits, backend authorization, or unlock server-controlled AI features. Experimental; device testing required.",
    default = false,
) {
    compatibleWith(compatibility())
    execute {
        requireExactPingo()
        val status = mutableClassDefBy(SUBSCRIPTION_STATUS).methods.singleOrNull {
            it.name == "isActive" && it.returnType == "Z" && it.parameterTypes.isEmpty() &&
                AccessFlags.PUBLIC.isSet(it.accessFlags) && !AccessFlags.STATIC.isSet(it.accessFlags)
        } ?: error("Reviewed Superwall SubscriptionStatus gate changed")
        val entitlement = mutableClassDefBy(ENTITLEMENT).methods.singleOrNull {
            it.name == "isActive" && it.returnType == "Z" && it.parameterTypes.isEmpty() &&
                AccessFlags.PUBLIC.isSet(it.accessFlags) && !AccessFlags.STATIC.isSet(it.accessFlags)
        } ?: error("Reviewed Superwall Entitlement gate changed")
        val statusBody = requireNotNull(status.implementation)
        val entitlementBody = requireNotNull(entitlement.implementation)
        val statusInstructions = statusBody.instructions.toList()
        val entitlementInstructions = entitlementBody.instructions.toList()
        require(statusBody.registerCount == 2 && statusInstructions.size == 2 &&
            statusInstructions[0].opcode == Opcode.INSTANCE_OF && statusInstructions[1].opcode == Opcode.RETURN &&
            (statusInstructions[0] as? ReferenceInstruction)?.reference.toString() == ACTIVE_STATUS
        ) { "Superwall SubscriptionStatus predicate changed or is already patched" }
        require(entitlementBody.registerCount == 2 && entitlementInstructions.size == 2 &&
            entitlementInstructions[0].opcode == Opcode.IGET_BOOLEAN && entitlementInstructions[1].opcode == Opcode.RETURN
        ) { "Superwall Entitlement predicate changed or is already patched" }
        status.addInstructions(0, "const/4 v0, 0x1\nreturn v0")
        entitlement.addInstructions(0, "const/4 v0, 0x1\nreturn v0")
    }
}
