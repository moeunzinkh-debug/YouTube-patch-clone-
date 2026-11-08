package app.morphe.patches.genv

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
private const val PROVIDER = "Lcom/pairip/licensecheck/LicenseContentProvider;"
private const val RESPONSE = "Lcom/pairip/licensecheck/LicenseResponseHelper;"
private const val CONTEXT = "Landroid/content/Context;"

/** Scoped to the reviewed GenV 3.7.2 (163) PairIP client-side methods. */
@Suppress("unused")
val removeLicenseCheckPatch = bytecodePatch(
    name = "Remove license check",
    description = "Disable the reviewed PairIP client-side Play license and installer entry points in GenV 3.7.2 (163). Does not grant purchases, subscriptions, server entitlements or bypass server attestation. Experimental; complete APK splits and device testing are required.",
    default = true,
) {
    compatibleWith(Compatibility(
        name = "GenV",
        packageName = "com.ainate.ai.video.generate",
        targets = listOf(AppTarget(version = "3.7.2", minSdk = 24, isExperimental = true)),
    ))

    execute {
        require(packageMetadata.packageName == "com.ainate.ai.video.generate" &&
            packageMetadata.versionName == "3.7.2" && packageMetadata.versionCode == "163") {
            "Remove license check supports only the reviewed GenV package, version 3.7.2 and build 163"
        }
        fun refs(method: com.android.tools.smali.dexlib2.iface.Method) = requireNotNull(method.implementation).instructions
            .mapNotNull { (it as? ReferenceInstruction)?.reference as? MethodReference }
        fun MethodReference.isMethod(owner: String, method: String, parameters: List<String>, result: String) =
            definingClass == owner && name == method && parameterTypes.map { it.toString() } == parameters && returnType == result

        val attach = mutableClassDefBy(APPLICATION).methods.singleOrNull {
            it.name == "attachBaseContext" && it.returnType == "V" &&
                it.parameterTypes.map { p -> p.toString() } == listOf(CONTEXT) && !AccessFlags.STATIC.isSet(it.accessFlags)
        } ?: error("Reviewed GenV application entry point not found")
        val attachBody = requireNotNull(attach.implementation)
        require(attachBody.registerCount == 2 && attachBody.instructions.map { it.opcode }.toList() ==
            listOf(Opcode.INVOKE_STATIC, Opcode.INVOKE_SUPER, Opcode.RETURN_VOID) &&
            refs(attach).any { it.isMethod(CLIENT, "checkLicense", listOf(CONTEXT), "V") }
        ) { "Reviewed application license call changed" }

        val provider = mutableClassDefBy(PROVIDER).methods.singleOrNull {
            it.name == "onCreate" && it.returnType == "Z" && it.parameterTypes.isEmpty() &&
                AccessFlags.PUBLIC.isSet(it.accessFlags) && !AccessFlags.STATIC.isSet(it.accessFlags)
        } ?: error("Reviewed GenV PairIP provider not found")
        val providerBody = requireNotNull(provider.implementation)
        require(providerBody.registerCount == 2 && providerBody.instructions.map { it.opcode }.toList() ==
            listOf(Opcode.INVOKE_VIRTUAL, Opcode.MOVE_RESULT_OBJECT, Opcode.INVOKE_STATIC, Opcode.CONST_4, Opcode.RETURN) &&
            refs(provider).any { it.isMethod(CLIENT, "checkLicense", listOf(CONTEXT), "V") }
        ) { "Reviewed provider license call changed" }

        val client = mutableClassDefBy(CLIENT)
        val check = client.methods.singleOrNull {
            it.name == "checkLicense" && it.returnType == "V" &&
                it.parameterTypes.map { p -> p.toString() } == listOf(CONTEXT) &&
                AccessFlags.PUBLIC.isSet(it.accessFlags) && AccessFlags.STATIC.isSet(it.accessFlags) &&
                !AccessFlags.NATIVE.isSet(it.accessFlags) && !AccessFlags.ABSTRACT.isSet(it.accessFlags)
        } ?: error("Reviewed GenV checkLicense method not found")
        val initialize = client.methods.singleOrNull {
            it.name == "initializeLicenseCheck" && it.returnType == "V" && it.parameterTypes.isEmpty() &&
                AccessFlags.PUBLIC.isSet(it.accessFlags) && !AccessFlags.STATIC.isSet(it.accessFlags) &&
                !AccessFlags.NATIVE.isSet(it.accessFlags) && !AccessFlags.ABSTRACT.isSet(it.accessFlags)
        } ?: error("Reviewed GenV initializeLicenseCheck method not found")

        val checkBody = requireNotNull(check.implementation)
        val checkOps = checkBody.instructions.map { it.opcode }.toList()
        require(checkBody.registerCount == 3 && checkOps == listOf(
            Opcode.CONST_STRING, Opcode.IF_NEZ, Opcode.CONST_STRING, Opcode.INVOKE_STATIC, Opcode.RETURN_VOID,
            Opcode.INVOKE_STATIC, Opcode.MOVE_RESULT, Opcode.IF_EQZ, Opcode.CONST_STRING, Opcode.INVOKE_STATIC,
            Opcode.RETURN_VOID, Opcode.SGET_OBJECT, Opcode.NEW_INSTANCE, Opcode.INVOKE_DIRECT, Opcode.INVOKE_INTERFACE, Opcode.RETURN_VOID
        ) && refs(check).any { it.isMethod(CLIENT, "isIsolatedProcess", emptyList(), "Z") } &&
            refs(check).any { it.isMethod("Lcom/pairip/licensecheck/LicenseClient\$ImmediateTaskExecutor;", "run", listOf("Ljava/lang/Runnable;"), "V") }
        ) { "GenV checkLicense implementation changed or is already patched" }

        val initBody = requireNotNull(initialize.implementation)
        val initOps = initBody.instructions.map { it.opcode }.toList()
        require(initBody.registerCount == 4 && initOps == listOf(
            Opcode.SGET_OBJECT, Opcode.INVOKE_VIRTUAL, Opcode.MOVE_RESULT, Opcode.CONST_4, Opcode.IF_EQZ,
            Opcode.CONST_4, Opcode.IF_EQ, Opcode.CONST_4, Opcode.IF_EQ, Opcode.RETURN_VOID,
            Opcode.INVOKE_DIRECT, Opcode.RETURN_VOID, Opcode.SGET_OBJECT, Opcode.SGET_OBJECT, Opcode.INVOKE_STATIC,
            Opcode.RETURN_VOID, Opcode.MOVE_EXCEPTION, Opcode.INVOKE_DIRECT, Opcode.RETURN_VOID, Opcode.SGET_BOOLEAN,
            Opcode.IF_EQZ, Opcode.SGET_BOOLEAN, Opcode.IF_NEZ, Opcode.SGET_OBJECT, Opcode.NEW_INSTANCE,
            Opcode.INVOKE_DIRECT, Opcode.INVOKE_INTERFACE, Opcode.RETURN_VOID, Opcode.INVOKE_DIRECT, Opcode.RETURN_VOID
        ) && refs(initialize).any { it.isMethod(RESPONSE, "validateResponse", listOf("Landroid/os/Bundle;", "Ljava/lang/String;"), "V") } &&
            refs(initialize).any { it.isMethod(CLIENT, "initiateFreshLicensingServiceConnection", listOf("Z"), "V") }
        ) { "GenV initializeLicenseCheck implementation changed or is already patched" }

        // Suppress these two reviewed client-side entry points. Do not forge a
        // Play result or change purchases, server entitlement or attestation.
        check.addInstruction(0, "return-void")
        initialize.addInstruction(0, "return-void")
    }
}
