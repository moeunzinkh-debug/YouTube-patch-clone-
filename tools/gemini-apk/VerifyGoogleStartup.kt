import com.android.tools.smali.dexlib2.Opcodes
import com.android.tools.smali.dexlib2.Opcode
import com.android.tools.smali.dexlib2.dexbacked.DexBackedDexFile
import com.android.tools.smali.dexlib2.iface.instruction.*
import java.util.zip.ZipFile

/** Focused structural check, not a substitute for Android verification/runtime. */
fun main(args: Array<String>) {
    var found = false
    ZipFile(args.single()).use { zip ->
        for (entry in zip.entries().asSequence().filter { it.name.matches(Regex("classes[0-9]*\\.dex")) }) {
            val dex = zip.getInputStream(entry).buffered().use { DexBackedDexFile.fromInputStream(Opcodes.getDefault(), it) }
            val cls = dex.classes.firstOrNull { it.type == "Ldgtr;" } ?: continue
            val method = cls.methods.single { it.name == "b" && it.parameterTypes.isEmpty() && it.returnType == "Ljava/lang/String;" }
            val impl = requireNotNull(method.implementation)
            check(impl.registerCount >= 4)
            val instructions = impl.instructions.toList()
            check(instructions.count { it.opcode == Opcode.RETURN_OBJECT } == 2)
            val calls = instructions.indices.filter {
                (instructions[it] as? ReferenceInstruction)?.reference.toString() ==
                    "Ljava/lang/String;->replace(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Ljava/lang/String;"
            }
            check(calls.size == 2)
            for (index in calls) {
                val guard = instructions[index - 3]
                check(guard.opcode == Opcode.IF_EQZ)
                val invoke = instructions[index] as FiveRegisterInstruction
                check((guard as OneRegisterInstruction).registerA == invoke.registerC)
                check(invoke.registerC != invoke.registerD && invoke.registerC != invoke.registerE)
                check(invoke.registerD != invoke.registerE)
                for (reg in listOf(invoke.registerC, invoke.registerD, invoke.registerE)) check(reg < impl.registerCount)
                // Branch must skip the replacement and land on its following nop.
                check((guard as OffsetInstruction).codeOffset == instructions.subList(index - 3, index + 2).sumOf { it.codeUnits })
                check(instructions[index + 2].opcode == Opcode.NOP)
            }
            found = true
            println("Google process provider: two null-guarded replacements, valid scratch registers and branch targets")
        }
    }
    check(found) { "Google process provider missing in patched output" }
}
