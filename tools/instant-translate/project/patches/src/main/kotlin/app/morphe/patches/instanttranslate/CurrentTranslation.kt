package app.morphe.patches.instanttranslate

import app.morphe.patcher.extensions.InstructionExtensions.addInstruction
import app.morphe.patcher.extensions.InstructionExtensions.addInstructionsWithLabels
import app.morphe.patcher.extensions.InstructionExtensions.getInstruction
import app.morphe.patcher.extensions.InstructionExtensions.removeInstruction
import app.morphe.patcher.extensions.InstructionExtensions.replaceInstruction
import app.morphe.patcher.patch.BytecodePatchContext
import app.morphe.patcher.util.proxy.mutableTypes.MutableMethod
import com.android.tools.smali.dexlib2.AccessFlags
import com.android.tools.smali.dexlib2.Opcode
import com.android.tools.smali.dexlib2.iface.instruction.Instruction
import com.android.tools.smali.dexlib2.iface.instruction.ReferenceInstruction
import com.android.tools.smali.dexlib2.iface.instruction.TwoRegisterInstruction
import com.android.tools.smali.dexlib2.iface.reference.FieldReference
import com.android.tools.smali.dexlib2.iface.reference.MethodReference

private const val FALLBACK = "Lapp/morphe/extension/instanttranslate/TranslationFallback;"

private fun MutableMethod.insertPreservingLabel(index: Int, text: String) {
    addInstruction(index + 1, getInstruction(index))
    addInstructionsWithLabels(index + 1, text)
    removeInstruction(index)
}

/** Hook the reviewed final empty single-translation result, not all app sections. */
internal fun BytecodePatchContext.applyCurrentTranslation() {
    val owner = mutableClassDefBy("Lz37;")
    val token = mutableClassDefBy("Lfra;")
    require(listOf("t", "u", "v").all { name ->
        token.fields.any { it.name == name && it.type == "Ljava/lang/String;" }
    }) { "Reviewed v7.5.00307 translation coroutine fields changed" }
    val translate = owner.methods.singleOrNull {
        it.name == "A" && it.returnType == "Ljava/lang/Object;" && AccessFlags.STATIC.isSet(it.accessFlags) &&
            it.parameterTypes.map { p -> p.toString() } == listOf("Ljava/lang/String;", "Ljava/lang/String;", "Ljava/lang/String;", "Lip2;")
    } ?: error("Reviewed v7.5.00307 translation method was not found")
    val interceptor = mutableClassDefBy("Lgia;").methods.singleOrNull {
        it.name == "x" && it.returnType == "Lhp2;" && AccessFlags.STATIC.isSet(it.accessFlags) &&
            it.parameterTypes.map { p -> p.toString() } == listOf("Lhp2;")
    } ?: error("Reviewed v7.5.00307 coroutine interceptor was not found")
    val ti = requireNotNull(translate.implementation).instructions.toList()
    val ii = requireNotNull(interceptor.implementation).instructions.toList()
    fun methodAt(instructions: List<Instruction>, index: Int, ownerName: String, name: String): Boolean {
        val ref = (instructions[index] as? ReferenceInstruction)?.reference as? MethodReference
        return ref?.definingClass == ownerName && ref.name == name
    }
    fun fieldAt(index: Int, name: String): Boolean {
        val ref = (ti[index] as? ReferenceInstruction)?.reference as? FieldReference
        return ref?.definingClass == "Lfra;" && ref.name == name
    }
    require(translate.implementation!!.registerCount == 13 && ti.size == 132 &&
        (117..119).all { ti[it].opcode == Opcode.IPUT_OBJECT && (ti[it] as? TwoRegisterInstruction)?.registerA == 6 } &&
        fieldAt(117, "t") && fieldAt(118, "u") && fieldAt(119, "v") &&
        methodAt(ti, 121, "Lz37;", "D") && ti[125].opcode == Opcode.CHECK_CAST &&
        methodAt(ti, 126, "Lq1a;", "s0") && ti[130].opcode == Opcode.CONST_STRING && ti[131].opcode == Opcode.RETURN_OBJECT
    ) { "Reviewed v7.5.00307 translation failure path changed" }
    require(ii.size == 14 && methodAt(ii, 8, "Lip2;", "intercepted")) {
        "Reviewed v7.5.00307 continuation interception changed"
    }
    // v11 is text, v10 source and v9 target at this last native retry. Keep
    // them on its existing coroutine until completion, instead of clearing them.
    // Insert at the labelled final failure path in descending index order.
    translate.insertPreservingLabel(130, """
        invoke-static {v0}, Lgia;->x(Lhp2;)Lhp2;
        move-result-object v1
        invoke-static {v12, v0, v1}, $FALLBACK->retryAfterBlank(Ljava/lang/String;Ljava/lang/Object;Ljava/lang/Object;)Z
        move-result v1
        if-eqz v1, :native_failure
        return-object v7
        :native_failure
        nop
    """.trimIndent())
    translate.replaceInstruction(117, "iput-object v11, v0, Lfra;->t:Ljava/lang/String;")
    translate.replaceInstruction(118, "iput-object v10, v0, Lfra;->u:Ljava/lang/String;")
    translate.replaceInstruction(119, "iput-object v9, v0, Lfra;->v:Ljava/lang/String;")
}
