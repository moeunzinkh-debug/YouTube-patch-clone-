package app.morphe.patches.instanttranslate

import app.morphe.patcher.extensions.InstructionExtensions.addInstruction
import app.morphe.patcher.extensions.InstructionExtensions.addInstructionsWithLabels
import app.morphe.patcher.extensions.InstructionExtensions.getInstruction
import app.morphe.patcher.extensions.InstructionExtensions.removeInstruction
import app.morphe.patcher.extensions.InstructionExtensions.replaceInstruction
import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.bytecodePatch
import app.morphe.patcher.util.proxy.mutableTypes.MutableField.Companion.toMutable
import app.morphe.patcher.util.proxy.mutableTypes.MutableMethod
import com.android.tools.smali.dexlib2.AccessFlags
import com.android.tools.smali.dexlib2.Opcode
import com.android.tools.smali.dexlib2.iface.instruction.FiveRegisterInstruction
import com.android.tools.smali.dexlib2.iface.instruction.ReferenceInstruction
import com.android.tools.smali.dexlib2.iface.instruction.TwoRegisterInstruction
import com.android.tools.smali.dexlib2.iface.reference.FieldReference
import com.android.tools.smali.dexlib2.iface.reference.MethodReference
import com.android.tools.smali.dexlib2.immutable.ImmutableField

private const val EXTENSION = "Lapp/morphe/extension/instanttranslate/TranslationFallback;"
private const val CONTINUATION = "Ltk3;->Q(Llx1;)Llx1;"

// Adapted from MorpheApp/morphe-patches-library BytecodeUtils (GPL-3.0).
// Move the existing control-flow label onto the first inserted instruction.
private fun MutableMethod.addInstructionsAtControlFlowLabel(index: Int, instructions: String) {
    addInstruction(index + 1, getInstruction(index))
    addInstructionsWithLabels(index + 1, instructions)
    removeInstruction(index)
}

private val translationExtensionPatch = bytecodePatch {
    extendWith("extensions/instanttranslate.mpe")
}

@Suppress("unused")
val translationFallbackPatch = bytecodePatch(
    name = "Translation fallback (SEA-LION, experimental)",
    description = "Keep original translation first. An explicitly configured SEA-LION provider can retry reviewed blank results; default is original only. Requires internet, a user-supplied key and data sharing. Reviewed builds 50342 and 50350; coverage and device runtime unverified.",
    default = false,
) {
    compatibleWith(Compatibility(
        name = "Instant Translate", packageName = "com.spaceship.screen.textcopy",
        targets = listOf(
            AppTarget(version = "v7.5.00300", minSdk = 29, isExperimental = true),
            AppTarget(version = "v7.5.00307", minSdk = 29, isExperimental = true),
        ),
    ))
    dependsOn(translationExtensionPatch)
    execute {
        if (packageMetadata.versionName == "v7.5.00307" && packageMetadata.versionCode == "50350") {
            applyCurrentTranslation()
            return@execute
        }
        require(packageMetadata.versionName == "v7.5.00300" && packageMetadata.versionCode == "50342") {
            "Translation fallback supports only reviewed Instant Translate v7.5.00300 / 50342"
        }
        val singleClass = mutableClassDefBy("Lbe4;")
        val endpointClass = mutableClassDefBy("Lkb9;")
        val batchClass = mutableClassDefBy("Lxm;")
        val singleContinuation = mutableClassDefBy("Ld29;")
        val endpointContinuation = mutableClassDefBy("Lqy8;")
        val batchContinuation = mutableClassDefBy("Lmr0;")
        require(singleContinuation.fields.any { it.name == "t" && it.type == "Ljava/lang/String;" } &&
            endpointContinuation.fields.filter { it.name in setOf("t", "u", "v") && it.type == "Ljava/lang/String;" }.size == 3 &&
            batchContinuation.fields.any { it.name == "t" && it.type == "Leh7;" }
        ) { "Reviewed coroutine fields changed" }
        require(singleContinuation.fields.none { it.name == "morphe_source" || it.name == "morphe_target" }) {
            "Translation fallback is already installed"
        }

        val single = singleClass.methods.singleOrNull {
            it.name == "g0" && it.returnType == "Ljava/lang/Object;" &&
                it.parameterTypes.map { p -> p.toString() } == listOf("Ljava/lang/String;", "Ljava/lang/String;", "Ljava/lang/String;", "Lmx1;") &&
                AccessFlags.STATIC.isSet(it.accessFlags)
        } ?: error("Single-result translation method does not match")
        val endpoint = endpointClass.methods.singleOrNull {
            it.name == "S" && it.returnType == "Ljava/lang/Object;" &&
                it.parameterTypes.map { p -> p.toString() } == listOf("Ljava/lang/String;", "Ljava/lang/String;", "Ljava/lang/String;", "Lmx1;") &&
                AccessFlags.STATIC.isSet(it.accessFlags)
        } ?: error("Endpoint translation method does not match")
        val batch = batchClass.methods.singleOrNull {
            it.name == "D" && it.returnType == "Ljava/lang/Object;" &&
                it.parameterTypes.map { p -> p.toString() } == listOf("Ljava/util/List;", "Ljava/lang/String;", "Ljava/lang/String;", "Leh7;", "Lmx1;") &&
                AccessFlags.STATIC.isSet(it.accessFlags)
        } ?: error("Batch translation method does not match")
        val a = requireNotNull(single.implementation)
        val b = requireNotNull(endpoint.implementation)
        val c = requireNotNull(batch.implementation)
        val ai = a.instructions.toList()
        val bi = b.instructions.toList()
        val ci = c.instructions.toList()
        require(a.registerCount == 10 && ai.size == 86 && b.registerCount == 13 && bi.size == 132 &&
            c.registerCount == 25 && ci.size == 127) { "Reviewed translation code/register layout changed" }

        fun methodAt(instructions: List<com.android.tools.smali.dexlib2.iface.instruction.Instruction>,
                     index: Int, owner: String, name: String): Boolean {
            val ref = (instructions[index] as? ReferenceInstruction)?.reference as? MethodReference
            return ref?.definingClass == owner && ref.name == name
        }
        fun fieldAt(instructions: List<com.android.tools.smali.dexlib2.iface.instruction.Instruction>,
                    index: Int, owner: String, name: String): Boolean {
            val ref = (instructions[index] as? ReferenceInstruction)?.reference as? FieldReference
            return ref?.definingClass == owner && ref.name == name
        }
        val constructor = ai[65] as? FiveRegisterInstruction
        require(methodAt(ai, 65, "Lus9;", "<init>") && ai[65].opcode == Opcode.INVOKE_DIRECT &&
            constructor != null && constructor.registerC == 9 && constructor.registerD == 6 && constructor.registerE == 7 && constructor.registerF == 8 &&
            methodAt(ai, 84, "Lbe4;", "Z") && ai[83].opcode == Opcode.SGET_OBJECT && ai[85].opcode == Opcode.RETURN_OBJECT
        ) { "Single-result translation continuation changed" }
        require(methodAt(bi, 121, "Lkb9;", "V") && bi[130].opcode == Opcode.CONST_STRING && bi[131].opcode == Opcode.RETURN_OBJECT &&
            (117..119).all { bi[it].opcode == Opcode.IPUT_OBJECT && (bi[it] as? TwoRegisterInstruction)?.registerA == 6 } &&
            fieldAt(bi, 117, "Lqy8;", "t") && fieldAt(bi, 118, "Lqy8;", "u") && fieldAt(bi, 119, "Lqy8;", "v")
        ) { "Endpoint continuation or final failure path changed" }
        require(fieldAt(ci, 14, "Lmr0;", "u") && ci[14].opcode == Opcode.IGET_OBJECT &&
            methodAt(ci, 39, "Lxm;", "E") && ci[44].opcode == Opcode.CHECK_CAST &&
            methodAt(ci, 45, "Ljava/util/List;", "isEmpty")
        ) { "Batch-result continuation changed" }

        // Store the already-normalized source and target in this specific single
        // translation coroutine. They are not global and are never logged.
        for (fieldName in listOf("morphe_source", "morphe_target")) {
            singleContinuation.fields.add(ImmutableField(
                "Ld29;", fieldName, "Ljava/lang/String;", AccessFlags.PUBLIC.value,
                null, null, null,
            ).toMutable())
        }

        // Insert in descending index order so validated original indices remain valid.
        // If a fallback starts, suspend and let the *intercepted* original
        // continuation resume on its original coroutine dispatcher.
        single.addInstructionsAtControlFlowLabel(84, """
            invoke-static {v0}, $CONTINUATION
            move-result-object v1
            invoke-static {v9, v0, v1}, $EXTENSION->retryAfterBlank(Ljava/lang/String;Ljava/lang/Object;Ljava/lang/Object;)Z
            move-result v1
            if-eqz v1, :native_result
            return-object v5
            :native_result
            nop
        """.trimIndent())
        single.addInstructionsAtControlFlowLabel(65, """
            iput-object v7, v0, Ld29;->morphe_source:Ljava/lang/String;
            iput-object v8, v0, Ld29;->morphe_target:Ljava/lang/String;
        """.trimIndent())

        endpoint.addInstructionsAtControlFlowLabel(130, """
            invoke-static {v0}, $CONTINUATION
            move-result-object v1
            invoke-static {v12, v0, v1}, $EXTENSION->retryAfterBlank(Ljava/lang/String;Ljava/lang/Object;Ljava/lang/Object;)Z
            move-result v1
            if-eqz v1, :native_failure
            return-object v7
            :native_failure
            nop
        """.trimIndent())
        // The original clears these before its final online attempt. Retain the
        // local request on the already-existing coroutine fields until it ends.
        endpoint.replaceInstruction(117, "iput-object v11, v0, Lqy8;->t:Ljava/lang/String;")
        endpoint.replaceInstruction(118, "iput-object v10, v0, Lqy8;->u:Ljava/lang/String;")
        endpoint.replaceInstruction(119, "iput-object v9, v0, Lqy8;->v:Ljava/lang/String;")

        batch.addInstructionsAtControlFlowLabel(45, """
            move-object/from16 v2, v18
            invoke-static {v2}, $CONTINUATION
            move-result-object v4
            invoke-static {v0, v1, v2, v4}, $EXTENSION->retryFailedBatch(Ljava/lang/Object;Ljava/util/List;Ljava/lang/Object;Ljava/lang/Object;)Z
            move-result v2
            if-eqz v2, :native_batch
            sget-object v2, Lkz1;->a:Lkz1;
            return-object v2
            :native_batch
            nop
        """.trimIndent())
        // v18 is unused before the batch-result branch and is reloaded on every
        // entry, including coroutine resumption. The empty batch is left to the
        // app's native per-item retry; successful elements are never replaced.
        batch.addInstructionsAtControlFlowLabel(15, "move-object/from16 v18, v1")
    }
}
