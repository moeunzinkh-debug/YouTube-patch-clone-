package app.morphe.patches.instanttranslate

import app.morphe.patcher.extensions.InstructionExtensions.addInstruction
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

/** Client-side PairIP entry points found by read-only inspection of build 50350. */
@Suppress("unused")
val removeInstantLicenseCheckPatch = bytecodePatch(
    name = "Remove license check (experimental)",
    description = "Disable the reviewed PairIP client-side Play licensing entry points in Instant Translate v7.5.00307 (50350). Weakens license/integrity protection; does not grant purchases or change server verification. Device runtime is untested.",
    default = false,
) {
    compatibleWith(Compatibility(
        name = "Instant Translate", packageName = "com.spaceship.screen.textcopy",
        targets = listOf(AppTarget(version = "v7.5.00307", minSdk = 29, isExperimental = true)),
    ))
    execute {
        require(packageMetadata.versionName == "v7.5.00307" && packageMetadata.versionCode == "50350") {
            "Remove license check supports only Instant Translate v7.5.00307 / 50350"
        }
        val application = mutableClassDefBy(PAIRIP_APPLICATION)
        val provider = mutableClassDefBy(PAIRIP_PROVIDER)
        val client = mutableClassDefBy(PAIRIP_CLIENT)
        val attach = application.methods.singleOrNull {
            it.name == "attachBaseContext" && it.returnType == "V" &&
                it.parameterTypes.map { p -> p.toString() } == listOf("Landroid/content/Context;")
        } ?: error("PairIP application entry point changed")
        val onCreate = provider.methods.singleOrNull {
            it.name == "onCreate" && it.returnType == "Z" && it.parameterTypes.isEmpty()
        } ?: error("PairIP provider entry point changed")
        val check = client.methods.singleOrNull {
            it.name == "checkLicense" && it.returnType == "V" &&
                it.parameterTypes.map { p -> p.toString() } == listOf("Landroid/content/Context;") &&
                AccessFlags.PUBLIC.isSet(it.accessFlags) && AccessFlags.STATIC.isSet(it.accessFlags)
        } ?: error("PairIP checkLicense changed")
        val initialize = client.methods.singleOrNull {
            it.name == "initializeLicenseCheck" && it.returnType == "V" && it.parameterTypes.isEmpty() &&
                AccessFlags.PUBLIC.isSet(it.accessFlags) && !AccessFlags.STATIC.isSet(it.accessFlags)
        } ?: error("PairIP initializeLicenseCheck changed")

        fun refs(method: app.morphe.patcher.util.proxy.mutableTypes.MutableMethod) =
            requireNotNull(method.implementation).instructions
                .mapNotNull { (it as? ReferenceInstruction)?.reference as? MethodReference }
        fun callsCheck(method: app.morphe.patcher.util.proxy.mutableTypes.MutableMethod) = refs(method).any {
            it.definingClass == PAIRIP_CLIENT && it.name == "checkLicense" && it.returnType == "V" &&
                it.parameterTypes.map { p -> p.toString() } == listOf("Landroid/content/Context;")
        }
        require(callsCheck(attach) && callsCheck(onCreate)) { "PairIP startup call sites changed" }
        val cb = requireNotNull(check.implementation)
        val ib = requireNotNull(initialize.implementation)
        val ci = cb.instructions.toList()
        val ii = ib.instructions.toList()
        require(cb.registerCount == 3 && ci.size == 16 && ci.first().opcode == Opcode.CONST_STRING &&
            refs(check).any { it.definingClass == PAIRIP_CLIENT && it.name == "isIsolatedProcess" && it.returnType == "Z" }
        ) { "PairIP checkLicense layout changed or was already patched" }
        require(ib.registerCount == 4 && ii.size == 30 && ii.first().opcode == Opcode.SGET_OBJECT &&
            refs(initialize).any { it.definingClass == PAIRIP_RESPONSE && it.name == "validateResponse" } &&
            refs(initialize).any { it.definingClass == PAIRIP_CLIENT && it.name == "initiateFreshLicensingServiceConnection" }
        ) { "PairIP initialization layout changed or was already patched" }

        // Do not forge a license response or change the publisher's server.
        check.addInstruction(0, "return-void")
        initialize.addInstruction(0, "return-void")
    }
}
