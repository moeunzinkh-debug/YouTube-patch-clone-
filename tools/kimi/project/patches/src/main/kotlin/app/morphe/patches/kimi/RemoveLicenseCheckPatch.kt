package app.morphe.patches.kimi

import app.morphe.patcher.extensions.InstructionExtensions.addInstruction
import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.bytecodePatch
import com.android.tools.smali.dexlib2.AccessFlags
import com.android.tools.smali.dexlib2.Opcode
import com.android.tools.smali.dexlib2.iface.instruction.ReferenceInstruction
import com.android.tools.smali.dexlib2.iface.reference.MethodReference

private const val APPLICATION = "Lcom/pairip/application/Application;"
private const val CLIENT = "Lcom/pairip/licensecheck/LicenseClient;"
private const val RESPONSE = "Lcom/pairip/licensecheck/LicenseResponseHelper;"

/**
 * Scoped to the reviewed Kimi 3.1.5 / 381 PairIP implementation.
 * This disables client-side license checks, not server entitlements or attestation.
 */
@Suppress("unused")
val removeLicenseCheckPatch = bytecodePatch(
    name = "Remove license check",
    description = "Disables the reviewed PairIP client-side Play license and installer check in Kimi 3.1.5 (381). Does not grant subscriptions or bypass server-side attestation. Experimental; device testing required.",
    default = true,
) {
    compatibleWith(Compatibility(
        name = "Kimi AI",
        packageName = "com.moonshot.kimichat",
        targets = listOf(AppTarget(version = "3.1.5", minSdk = 26, isExperimental = true)),
    ))

    execute {
        require(packageMetadata.versionName == "3.1.5" && packageMetadata.versionCode == "381") {
            "Remove license check supports only the reviewed Kimi 3.1.5 build 381"
        }

        val application = mutableClassDefBy(APPLICATION)
        val attach = application.methods.singleOrNull { method ->
            method.name == "attachBaseContext" && method.returnType == "V" &&
                method.parameterTypes.map { it.toString() } == listOf("Landroid/content/Context;")
        } ?: error("PairIP application entry point does not match the reviewed build")
        val attachRefs = requireNotNull(attach.implementation).instructions
            .mapNotNull { (it as? ReferenceInstruction)?.reference as? MethodReference }
        require(attachRefs.any { ref ->
            ref.definingClass == CLIENT && ref.name == "checkLicense" &&
                ref.parameterTypes.map { it.toString() } == listOf("Landroid/content/Context;") && ref.returnType == "V"
        }) { "PairIP application no longer invokes the reviewed license check" }

        val client = mutableClassDefBy(CLIENT)
        val check = client.methods.singleOrNull { method ->
            method.name == "checkLicense" && method.returnType == "V" &&
                method.parameterTypes.map { it.toString() } == listOf("Landroid/content/Context;") &&
                AccessFlags.PUBLIC.isSet(method.accessFlags) && AccessFlags.STATIC.isSet(method.accessFlags)
        } ?: error("PairIP checkLicense method does not match the reviewed build")
        val initialize = client.methods.singleOrNull { method ->
            method.name == "initializeLicenseCheck" && method.returnType == "V" && method.parameterTypes.isEmpty() &&
                AccessFlags.PUBLIC.isSet(method.accessFlags) && !AccessFlags.STATIC.isSet(method.accessFlags)
        } ?: error("PairIP initializeLicenseCheck method does not match the reviewed build")

        val checkBody = requireNotNull(check.implementation)
        val initBody = requireNotNull(initialize.implementation)
        val checkInstructions = checkBody.instructions.toList()
        val initInstructions = initBody.instructions.toList()
        val checkRefs = checkInstructions.mapNotNull { (it as? ReferenceInstruction)?.reference as? MethodReference }
        val initRefs = initInstructions.mapNotNull { (it as? ReferenceInstruction)?.reference as? MethodReference }
        require(checkBody.registerCount == 3 && checkInstructions.size == 16 &&
            checkInstructions.firstOrNull()?.opcode == Opcode.CONST_STRING &&
            checkRefs.any { it.definingClass == CLIENT && it.name == "isIsolatedProcess" && it.returnType == "Z" }
        ) { "PairIP checkLicense implementation changed or is already patched" }
        require(initBody.registerCount == 4 && initInstructions.size == 29 &&
            initInstructions.firstOrNull()?.opcode == Opcode.SGET_OBJECT &&
            initRefs.any { it.definingClass == RESPONSE && it.name == "validateResponse" } &&
            initRefs.any { it.definingClass == CLIENT && it.name == "initiateFreshLicensingServiceConnection" }
        ) { "PairIP initializeLicenseCheck implementation changed or is already patched" }

        // Both examined entry points are gated before scheduling or binding any
        // Play licensing work. No successful Play verdict or purchase is forged.
        check.addInstruction(0, "return-void")
        initialize.addInstruction(0, "return-void")
    }
}
