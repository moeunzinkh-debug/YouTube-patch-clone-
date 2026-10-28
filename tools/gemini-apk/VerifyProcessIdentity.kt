import com.android.tools.smali.dexlib2.Opcodes
import com.android.tools.smali.dexlib2.Opcode
import com.android.tools.smali.dexlib2.dexbacked.DexBackedDexFile
import com.android.tools.smali.dexlib2.iface.instruction.*
import com.android.tools.smali.dexlib2.iface.reference.StringReference
import java.util.zip.ZipFile

private const val ORIGINAL = "com.google.android.googlequicksearchbox"
private const val TARGET = "$ORIGINAL.morphe"
data class Snapshot(val names: List<String>, val literals: List<Int>, val callsHash: Boolean, val provider: List<String>?)
fun collect(path: String): Map<String, Snapshot> {
    val result = mutableMapOf<String, Snapshot>()
    ZipFile(path).use { zip ->
        for (entry in zip.entries().asSequence().filter { it.name.matches(Regex("classes[0-9]*\\.dex")) }) {
            val dex = zip.getInputStream(entry).buffered().use { DexBackedDexFile.fromInputStream(Opcodes.getDefault(), it) }
            for (cls in dex.classes) for (method in cls.methods) {
                val impl = method.implementation ?: continue
                val ins = impl.instructions.toList()
                val id = "${cls.type}->${method.name}(${method.parameterTypes.joinToString("")})${method.returnType}"
                val names = ins.mapNotNull { ((it as? ReferenceInstruction)?.reference as? StringReference)?.string }
                    .filter { it.startsWith("$ORIGINAL:") || it.startsWith("$TARGET:") }
                val provider = if (id == "Ldgtr;->b()Ljava/lang/String;") {
                    listOf("registers=${impl.registerCount}") + ins.map {
                        "${it.opcode}:${(it as? ReferenceInstruction)?.reference}:${(it as? OffsetInstruction)?.codeOffset}"
                    }
                } else null
                if (names.isEmpty() && provider == null) continue
                val literals = ins.filter { it.opcode in setOf(Opcode.CONST, Opcode.CONST_16, Opcode.CONST_4) }
                    .map { (it as NarrowLiteralInstruction).narrowLiteral }
                result[id] = Snapshot(names, literals, ins.any {
                    (it as? ReferenceInstruction)?.reference.toString() == "Ljava/lang/String;->hashCode()I"
                }, provider)
            }
        }
    }
    return result
}
fun main(args: Array<String>) {
    val before = collect(args[0]); val after = collect(args[1])
    var strings = 0; var hashes = 0
    check(before.keys == after.keys)
    for ((id, original) in before) {
        val patched = after.getValue(id)
        check(original.provider == patched.provider) { "Real process provider was modified: $id" }
        val expectedNames = original.names.map { TARGET + it.removePrefix(ORIGINAL) }
        check(patched.names == expectedNames) { "Process names disagree: $id" }
        strings += original.names.size
        val mapping = original.names.associate { it.hashCode() to (TARGET + it.removePrefix(ORIGINAL)).hashCode() }
        val expectedLiterals = original.literals.map { old ->
            if (original.callsHash && old in mapping) { hashes++; mapping.getValue(old) } else old
        }
        check(expectedLiterals == patched.literals) { "Process hash constants disagree: $id" }
    }
    check(strings > 0 && hashes > 0)
    check(before.values.any { it.provider != null })
    println("Verified process experiment: strings=$strings hashes=$hashes; native provider unchanged")
}
