package app.morphe.patches.instanttranslate

import app.morphe.patcher.extensions.InstructionExtensions.addInstruction
import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.bytecodePatch
import com.android.tools.smali.dexlib2.AccessFlags
import com.android.tools.smali.dexlib2.Opcode
import com.android.tools.smali.dexlib2.iface.instruction.ReferenceInstruction
import com.android.tools.smali.dexlib2.iface.reference.FieldReference
import com.android.tools.smali.dexlib2.iface.reference.MethodReference

/** Opt-in local entitlement gate only; never fabricates a RevenueCat or Play purchase. */
@Suppress("unused")
val unlockLocalPremiumPatch = bytecodePatch(
    name = "Unlock premium local gate (experimental)",
    description = "Force the reviewed local premium entitlement gate on in v7.5.00307 (50350). Does not create a subscription, alter RevenueCat/Google records, or unlock server-enforced services. Individual features and runtime have not been verified.",
    default = false,
) {
    compatibleWith(Compatibility(
        name = "Instant Translate", packageName = "com.spaceship.screen.textcopy",
        targets = listOf(AppTarget(version = "v7.5.00307", minSdk = 29, isExperimental = true)),
    ))
    execute {
        require(packageMetadata.versionName == "v7.5.00307" && packageMetadata.versionCode == "50350") {
            "Local premium gate supports only Instant Translate v7.5.00307 / 50350"
        }
        val gateClass = mutableClassDefBy("Lf0a;")
        require(listOf("a" to "Ljava/util/List;", "b" to "Ljava/util/Set;", "c" to "Ljava/util/List;").all { pair ->
            gateClass.fields.any { it.name == pair.first && it.type == pair.second }
        }) { "Local entitlement model changed" }
        val gate = gateClass.methods.singleOrNull {
            it.name == "a" && it.returnType == "Z" &&
                it.parameterTypes.map { p -> p.toString() } == listOf("Ljava/lang/String;") &&
                AccessFlags.PUBLIC.isSet(it.accessFlags) && !AccessFlags.STATIC.isSet(it.accessFlags)
        } ?: error("Local premium entitlement gate changed")
        val body = requireNotNull(gate.implementation)
        val ins = body.instructions.toList()
        fun fieldAt(index: Int, field: String): Boolean {
            val reference = (ins[index] as? ReferenceInstruction)?.reference as? FieldReference
            return reference?.definingClass == "Lf0a;" && reference.name == field
        }
        fun methodAt(index: Int, owner: String, name: String): Boolean {
            val reference = (ins[index] as? ReferenceInstruction)?.reference as? MethodReference
            return reference?.definingClass == owner && reference.name == name
        }
        require(body.registerCount == 5 && ins.size == 34 &&
            ins[0].opcode == Opcode.IGET_OBJECT && fieldAt(0, "c") &&
            ins[1].opcode == Opcode.IGET_OBJECT && fieldAt(1, "a") &&
            methodAt(8, "Ljava/util/Set;", "contains") &&
            methodAt(22, "Ljava/util/Collection;", "isEmpty") &&
            ins[31].opcode == Opcode.RETURN && ins[33].opcode == Opcode.RETURN
        ) { "Local entitlement gate layout changed or was already patched" }
        val modelInit = mutableClassDefBy("La86;").methods.singleOrNull {
            it.name == "<init>" && it.parameterTypes.map { p -> p.toString() } == listOf("Landroid/content/SharedPreferences;")
        } ?: error("Local entitlement state initializer changed")
        val initCallsGate = requireNotNull(modelInit.implementation).instructions.any {
            val reference = (it as? ReferenceInstruction)?.reference as? MethodReference
            reference?.definingClass == "Lf0a;" && reference.name == "a" && reference.returnType == "Z"
        }
        require(initCallsGate) { "Premium state no longer uses the reviewed local gate" }
        gate.addInstruction(0, "const/4 v0, 0x1")
        gate.addInstruction(1, "return v0")
    }
}
