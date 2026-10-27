import com.android.tools.smali.dexlib2.Opcodes
import com.android.tools.smali.dexlib2.dexbacked.DexBackedDexFile
import com.android.tools.smali.dexlib2.iface.instruction.*
import java.io.File
import java.security.MessageDigest
import java.util.zip.ZipFile

// Read-only discovery: deliberately accepts versions not registered for patching.
fun main(args: Array<String>) {
    require(args.size == 1) {
        "Usage: inspect-hooks.sh APK search REFERENCE_SUBSTRING | APK dump 'Lclass;->method(Args)Return'"
    }
    val apk = File(args[0])
    val digest = MessageDigest.getInstance("SHA-256")
    apk.inputStream().use { input ->
        val buffer = ByteArray(65536)
        while (true) { val n = input.read(buffer); if (n < 0) break; digest.update(buffer, 0, n) }
    }
    println("APK=${apk.name} sha256=${digest.digest().joinToString("") { "%02x".format(it) }}")
    var matches = 0
    ZipFile(apk).use { zip ->
        zip.entries().asSequence().filter { it.name.matches(Regex("classes[0-9]*\\.dex")) }.forEach { entry ->
            val dex = zip.getInputStream(entry).buffered().use { DexBackedDexFile.fromInputStream(Opcodes.getDefault(), it) }
            for (cls in dex.classes.sortedBy { it.type }) for (method in cls.methods) {
                val impl = method.implementation ?: continue
                val id = "${cls.type}->${method.name}(${method.parameterTypes.joinToString("")})${method.returnType}"
                val instructions = impl.instructions.toList()
                val anchors = listOf("Trampolining to web app for work profile", "Skipping trampoline to web app", "Robin eligibility :", "com.google.android.googlequicksearchbox:googleapp", "More than 1 custom main process specified", "requires Google Play services", "The Google Play services resources were not found", "Unable to obtain package certificate history.")
                val hits = instructions.indices.filter {
                    val ref = (instructions[it] as? ReferenceInstruction)?.reference?.toString().orEmpty()
                    anchors.any { a -> ref.contains(a) }
                }
                if (hits.isEmpty() && cls.type !in listOf("Ldgtr;", "Ldgtn;", "Lcdij;") && !(cls.type.endsWith("/robin/main/MainActivity;") && method.name == "onCreate")) continue
                matches++
                println("\n${entry.name} $id registers=${impl.registerCount} hits=${hits.size}")
                var offset = 0
                for ((index, insn) in instructions.withIndex()) {
                    if (true) {
                        val regs = when (insn) {
                            is RegisterRangeInstruction -> "v${insn.startRegister} count=${insn.registerCount}"
                            is FiveRegisterInstruction -> listOf(insn.registerC, insn.registerD, insn.registerE, insn.registerF, insn.registerG).take(insn.registerCount).joinToString { "v$it" }
                            is ThreeRegisterInstruction -> "v${insn.registerA},v${insn.registerB},v${insn.registerC}"
                            is TwoRegisterInstruction -> "v${insn.registerA},v${insn.registerB}"
                            is OneRegisterInstruction -> "v${insn.registerA}"
                            else -> ""
                        }
                        val ref = (insn as? ReferenceInstruction)?.reference?.toString().orEmpty().replace("\n", "\\n").replace("\r", "\\r")
                        val branch = (insn as? OffsetInstruction)?.let { " targetCodeUnit=${offset + it.codeOffset}" }.orEmpty()
                        val literal = (insn as? WideLiteralInstruction)?.let { " literal=${it.wideLiteral}" }.orEmpty()
                        println("index=$index codeUnit=$offset ${insn.opcode} $regs $ref$literal$branch")
                    }
                    offset += insn.codeUnits
                }
            }
        }
    }
    println("\nmatchedMethods=$matches (discovery only; not proof of a safe hook)")
    check(matches > 0) { "No matching method: inspect changed strings/callers; do not reuse old obfuscated names blindly" }
}
