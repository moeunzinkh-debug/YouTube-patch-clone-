package app.morphe.patches.instanttranslate

import app.morphe.patcher.extensions.InstructionExtensions.addInstruction
import app.morphe.patcher.extensions.InstructionExtensions.addInstructionsWithLabels
import app.morphe.patcher.extensions.InstructionExtensions.getInstruction
import app.morphe.patcher.extensions.InstructionExtensions.removeInstruction
import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.bytecodePatch
import app.morphe.patcher.util.proxy.mutableTypes.MutableMethod
import com.android.tools.smali.dexlib2.AccessFlags
import com.android.tools.smali.dexlib2.Opcode
import com.android.tools.smali.dexlib2.iface.instruction.NarrowLiteralInstruction
import com.android.tools.smali.dexlib2.iface.instruction.OneRegisterInstruction
import com.android.tools.smali.dexlib2.iface.instruction.ReferenceInstruction
import com.android.tools.smali.dexlib2.iface.instruction.TwoRegisterInstruction
import com.android.tools.smali.dexlib2.iface.reference.MethodReference

private const val SETTINGS = "Lapp/morphe/extension/instanttranslate/SettingsUi;"
private const val CLICK = "Lapp/morphe/extension/instanttranslate/SettingsClick;"

// Adapted from MorpheApp/morphe-patches-library BytecodeUtils (GPL-3.0).
private fun MutableMethod.addAtExistingLabel(index: Int, instructions: String) {
    addInstruction(index + 1, getInstruction(index))
    addInstructionsWithLabels(index + 1, instructions)
    removeInstruction(index)
}

@Suppress("unused")
val instantSettingsPatch = bytecodePatch(
    name = "Settings Patch (SEA-LION, experimental)",
    description = "Add an in-app Settings Patch row and selectable SEA-LION fallback. Requires a user-supplied API key; text and key are sent to the selected HTTPS provider. Exact v7.5.00300 build 50342 only.",
    default = false,
) {
    compatibleWith(Compatibility(
        name = "Instant Translate", packageName = "com.spaceship.screen.textcopy",
        targets = listOf(AppTarget(version = "v7.5.00300", minSdk = 29, isExperimental = true)),
    ))
    dependsOn(translationFallbackPatch)
    execute {
        require(packageMetadata.versionName == "v7.5.00300" && packageMetadata.versionCode == "50342") {
            "Settings Patch supports only reviewed Instant Translate v7.5.00300 / 50342"
        }
        val row = mutableClassDefBy("Ldv0;").methods.singleOrNull {
            it.name == "e" && it.returnType == "Ljava/lang/Object;" &&
                it.parameterTypes.map { p -> p.toString() } == listOf("Ljava/lang/Object;", "Ljava/lang/Object;", "Ljava/lang/Object;") &&
                !AccessFlags.STATIC.isSet(it.accessFlags)
        } ?: error("Reviewed Settings row method not found")
        val activity = mutableClassDefBy("Lcom/spaceship/screen/translate/ui/MainActivity;").methods.singleOrNull {
            it.name == "onCreate" && it.returnType == "V" && it.parameterTypes.map { p -> p.toString() } == listOf("Landroid/os/Bundle;")
        } ?: error("Reviewed main activity method not found")
        val application = mutableClassDefBy("Lcom/spaceship/screen/translate/SSApplication;").methods.singleOrNull {
            it.name == "onCreate" && it.returnType == "V" && it.parameterTypes.isEmpty()
        } ?: error("Reviewed application initialization method not found")
        val ri = requireNotNull(row.implementation).instructions.toList()
        val mi = requireNotNull(activity.implementation).instructions.toList()
        val ai = requireNotNull(application.implementation).instructions.toList()
        fun methodAt(instructions: List<com.android.tools.smali.dexlib2.iface.instruction.Instruction>,
                     index: Int, owner: String, name: String): Boolean {
            val ref = (instructions[index] as? ReferenceInstruction)?.reference as? MethodReference
            return ref?.definingClass == owner && ref.name == name
        }
        require(row.implementation!!.registerCount == 24 && ri.size == 177 &&
            ri[19].opcode == Opcode.CONST_4 && (ri[19] as? OneRegisterInstruction)?.registerA == 7 &&
            (ri[19] as? NarrowLiteralInstruction)?.narrowLiteral == 0 &&
            ri[28].opcode == Opcode.CONST && (ri[28] as? NarrowLiteralInstruction)?.narrowLiteral == 0x7f13046b &&
            ri[31].opcode == Opcode.CONST && (ri[31] as? NarrowLiteralInstruction)?.narrowLiteral == 0x7f13046c &&
            methodAt(ri, 29, "Lpa4;", "P") && methodAt(ri, 34, "Laa4;", "G") &&
            ri[63].opcode == Opcode.MOVE && (ri[63] as? TwoRegisterInstruction)?.registerA == 0 &&
            (ri[63] as? TwoRegisterInstruction)?.registerB == 7 &&
            ri[66].opcode == Opcode.INVOKE_STATIC_RANGE && methodAt(ri, 66, "Lu44;", "v")
        ) { "Reviewed Settings renderer changed" }
        require(activity.implementation!!.registerCount == 13 && mi.size == 129 &&
            methodAt(mi, 1, "Lbin/edisaputra/protector/LicenseActivity;", "verifyIntegrity") &&
            mi[14].opcode == Opcode.INVOKE_SUPER && methodAt(mi, 14, "Lwk1;", "onCreate") &&
            mi[15].opcode == Opcode.SPUT_OBJECT
        ) { "Reviewed activity startup changed" }
        require(application.implementation!!.registerCount == 5 && ai.size == 96 &&
            ai[0].opcode == Opcode.INVOKE_SUPER && methodAt(ai, 0, "Landroid/app/Application;", "onCreate")
        ) { "Reviewed application startup changed" }

        // Initialize only after the original super.onCreate; do not change or
        // bypass any existing integrity/license/entitlement checks.
        application.addAtExistingLabel(1, "invoke-static {v4}, $SETTINGS->initialize(Landroid/content/Context;)V")
        activity.addAtExistingLabel(15, "invoke-static {v11}, $SETTINGS->attach(Landroid/app/Activity;)V")

        // Reuse the app's existing Compose row renderer and icon. v0/v1/v2 and
        // the incoming receiver stay intact; save/restore v9 (composer) and
        // restore the original zero in v7, which the next rows still read.
        row.addAtExistingLabel(28, """
            move-object/from16 v16, v9
            const/4 v4, 0x0
            const-string v5, "Settings Patch"
            const/4 v6, 0x0
            const-string v7, "Translation providers"
            const/4 v8, 0x0
            new-instance v9, $CLICK
            invoke-direct {v9}, $CLICK-><init>()V
            const-wide/16 v10, 0x0
            const/4 v12, 0x0
            invoke-static {}, Laa4;->G()Lc64;
            move-result-object v13
            const-wide/16 v14, 0x0
            const/16 v17, 0x0
            const/16 v18, 1493
            invoke-static/range {v4 .. v18}, Lu44;->v(Lls5;Ljava/lang/String;Lhm3;Ljava/lang/String;Lhm3;Lkotlin/jvm/functions/Function0;JLjava/lang/String;Lc64;JLlo1;II)V
            move-object/from16 v9, v16
            const/4 v7, 0x0
        """.trimIndent())
    }
}
