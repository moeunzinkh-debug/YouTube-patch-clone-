package app.morphe.patches.google.workprofile

import app.morphe.patcher.extensions.InstructionExtensions.instructions
import app.morphe.patcher.extensions.InstructionExtensions.replaceInstruction
import app.morphe.patcher.patch.bytecodePatch
import app.morphe.patcher.StringComparisonType
import com.android.tools.smali.dexlib2.Opcode
import com.android.tools.smali.dexlib2.iface.instruction.*
import com.android.tools.smali.dexlib2.iface.reference.StringReference

/** Experimental identity-consistent switch rewrite. No process provider spoofing. */
val processIdentityPatch = bytecodePatch(
    name = "Google clone process identity (experimental)",
    description = "Keep real process names; rewrite exact process strings and same-method hash literals.",
    default = true
) {
    compatibleWith("com.google.android.googlequicksearchbox")
    execute {
        check(packageMetadata.versionName == "17.6.59.ve.arm64" && packageMetadata.versionCode == "301698282")
        val original = "com.google.android.googlequicksearchbox"
        val target = "$original.morphe"
        val prefix = "$original:"
        var strings = 0
        var hashes = 0
        val candidates = classDefByStrings(prefix, StringComparisonType.STARTS_WITH)
        for (clazz in candidates) {
            for (method in mutableClassDefBy(clazz).methods) {
                if (method.implementation == null) continue
                val ins = method.instructions.toList()
                val names = ins.mapNotNull { ((it as? ReferenceInstruction)?.reference as? StringReference)?.string }
                    .filter { it.startsWith(prefix) }.distinct()
                if (names.isEmpty()) continue
                val hashMap = names.associate { it.hashCode() to (target + it.removePrefix(original)).hashCode() }
                check(hashMap.values.distinct().size == hashMap.size) { "Process hash collision" }
                // Unrelated enum/id switches may coexist with process strings.
                // Reject only payload keys that actually encode one of these hashes.
                check(ins.filterIsInstance<SwitchPayload>().none { payload ->
                    payload.switchElements.any { hashMap.containsKey(it.key) }
                }) { "Process hash switch payload requires explicit key remapping: ${clazz.type}->${method.name}" }

                val comparesHash = ins.any { (it as? ReferenceInstruction)?.reference.toString() == "Ljava/lang/String;->hashCode()I" }
                for ((index, instruction) in ins.withIndex()) {
                    val value = ((instruction as? ReferenceInstruction)?.reference as? StringReference)?.string
                    if (value != null && value.startsWith(prefix)) {
                        val reg = (instruction as OneRegisterInstruction).registerA
                        val replacement = target + value.removePrefix(original)
                        val opcode = if (instruction.opcode == Opcode.CONST_STRING_JUMBO) "const-string/jumbo" else "const-string"
                        method.replaceInstruction(index, "$opcode v$reg, \"$replacement\"")
                        strings++
                    } else if (comparesHash && instruction.opcode in setOf(Opcode.CONST, Opcode.CONST_16, Opcode.CONST_4)) {
                        val old = (instruction as? NarrowLiteralInstruction)?.narrowLiteral ?: continue
                        val replacement = hashMap[old] ?: continue
                        val reg = (instruction as OneRegisterInstruction).registerA
                        method.replaceInstruction(index, "const v$reg, $replacement")
                        hashes++
                    }
                }
            }
        }
        check(strings > 0 && hashes > 0) { "No process/hash mapping; refusing empty experimental patch" }
        println("[Experimental process identity] strings=$strings hashes=$hashes; provider untouched")
    }
}
