package app.morphe.patches.instanttranslate

import app.morphe.patcher.extensions.InstructionExtensions.addInstruction
import app.morphe.patcher.extensions.InstructionExtensions.addInstructionsWithLabels
import app.morphe.patcher.extensions.InstructionExtensions.getInstruction
import app.morphe.patcher.extensions.InstructionExtensions.removeInstruction
import app.morphe.patcher.patch.BytecodePatchContext
import app.morphe.patcher.util.proxy.mutableTypes.MutableMethod
import com.android.tools.smali.dexlib2.AccessFlags
import com.android.tools.smali.dexlib2.Opcode
import com.android.tools.smali.dexlib2.iface.instruction.Instruction
import com.android.tools.smali.dexlib2.iface.instruction.NarrowLiteralInstruction
import com.android.tools.smali.dexlib2.iface.instruction.ReferenceInstruction
import com.android.tools.smali.dexlib2.iface.reference.MethodReference

private const val UI = "Lapp/morphe/extension/instanttranslate/SettingsUi;"
private const val CALLBACK = "Lapp/morphe/extension/instanttranslate/CurrentSettingsClick;"

private fun MutableMethod.insertAtExistingLabel(index: Int, instructions: String) {
    addInstruction(index + 1, getInstruction(index))
    addInstructionsWithLabels(index + 1, instructions)
    removeInstruction(index)
}

internal fun BytecodePatchContext.applyCurrentSettings() {
    val row = mutableClassDefBy("Lze0;").methods.singleOrNull {
        it.name == "o" && it.returnType == "Ljava/lang/Object;" &&
            it.parameterTypes.map { p -> p.toString() } == listOf("Ljava/lang/Object;", "Ljava/lang/Object;", "Ljava/lang/Object;") &&
            !AccessFlags.STATIC.isSet(it.accessFlags)
    } ?: error("Reviewed v7.5.00307 Settings row was not found")
    val activity = mutableClassDefBy("Lcom/spaceship/screen/translate/ui/MainActivity;").methods.singleOrNull {
        it.name == "onCreate" && it.returnType == "V" && it.parameterTypes.map { p -> p.toString() } == listOf("Landroid/os/Bundle;")
    } ?: error("Reviewed v7.5.00307 main activity was not found")
    val application = mutableClassDefBy("Lcom/spaceship/screen/translate/SSApplication;").methods.singleOrNull {
        it.name == "onCreate" && it.returnType == "V" && it.parameterTypes.isEmpty()
    } ?: error("Reviewed v7.5.00307 application initialization was not found")
    val rowInstructions = requireNotNull(row.implementation).instructions.toList()
    val activityInstructions = requireNotNull(activity.implementation).instructions.toList()
    val appInstructions = requireNotNull(application.implementation).instructions.toList()
    fun methodAt(instructions: List<Instruction>, index: Int, owner: String, name: String): Boolean {
        val ref = (instructions[index] as? ReferenceInstruction)?.reference as? MethodReference
        return ref?.definingClass == owner && ref.name == name
    }
    require(row.implementation!!.registerCount == 27 && rowInstructions.size == 249 &&
        (rowInstructions[120] as? NarrowLiteralInstruction)?.narrowLiteral == 0x7f1305e3 &&
        (rowInstructions[123] as? NarrowLiteralInstruction)?.narrowLiteral == 0x7f1305e4 &&
        methodAt(rowInstructions, 118, "Liw6;", "b") && methodAt(rowInstructions, 121, "Lde4;", "l") &&
        methodAt(rowInstructions, 126, "Lf23;", "M0") && methodAt(rowInstructions, 149, "Liw6;", "b")
    ) { "Reviewed v7.5.00307 Settings renderer changed" }
    require(activity.implementation!!.registerCount == 13 && activityInstructions.size == 127 &&
        activityInstructions[11].opcode == Opcode.INVOKE_SUPER && methodAt(activityInstructions, 11, "Lmc2;", "onCreate") &&
        activityInstructions[12].opcode == Opcode.SPUT_OBJECT
    ) { "Reviewed v7.5.00307 activity startup changed" }
    require(application.implementation!!.registerCount == 5 && appInstructions.size == 100 &&
        appInstructions[0].opcode == Opcode.INVOKE_SUPER && methodAt(appInstructions, 0, "Landroid/app/Application;", "onCreate")
    ) { "Reviewed v7.5.00307 application startup changed" }

    application.insertAtExistingLabel(1, "invoke-static {v4}, $UI->initialize(Landroid/content/Context;)V")
    activity.insertAtExistingLabel(12, "invoke-static {v11}, $UI->attach(Landroid/app/Activity;)V")
    // At this exact point v19 is dead and v0/v1/v2/v3/v22/v23 are live.
    // Save the composer in v19, reuse the app row renderer, then restore v9.
    row.insertAtExistingLabel(120, """
        move-object/from16 v19, v9
        const/4 v4, 0x0
        const-string v5, "Settings Patch"
        const/4 v6, 0x0
        const-string v7, "Translation providers"
        const/4 v8, 0x0
        new-instance v9, $CALLBACK
        invoke-direct {v9}, $CALLBACK-><init>()V
        const-wide/16 v10, 0x0
        const/4 v12, 0x0
        invoke-static {}, Lf23;->M0()Ld65;
        move-result-object v13
        const-wide/16 v14, 0x0
        move-object/from16 v16, v19
        const/16 v17, 0x0
        const/16 v18, 1493
        invoke-static/range {v4 .. v18}, Liw6;->b(Lz47;Ljava/lang/String;Llh4;Ljava/lang/String;Llh4;Lkotlin/jvm/functions/Function0;JLjava/lang/String;Ld65;JLfg2;II)V
        move-object/from16 v9, v19
    """.trimIndent())
}
