package app.morphe.patches.king

import app.morphe.patcher.extensions.InstructionExtensions.addInstructions
import app.morphe.patcher.extensions.InstructionExtensions.addInstructionsWithLabels
import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.bytecodePatch
import com.android.tools.smali.dexlib2.AccessFlags
import com.android.tools.smali.dexlib2.Opcode
import com.android.tools.smali.dexlib2.iface.instruction.FiveRegisterInstruction
import com.android.tools.smali.dexlib2.iface.instruction.OneRegisterInstruction
import com.android.tools.smali.dexlib2.iface.instruction.ReferenceInstruction
import com.android.tools.smali.dexlib2.iface.instruction.TwoRegisterInstruction
import com.android.tools.smali.dexlib2.iface.reference.MethodReference
import com.android.tools.smali.dexlib2.iface.reference.FieldReference
import com.android.tools.smali.dexlib2.iface.reference.TypeReference

private const val PACKAGE = "ru.jgaiecip.osuojvyxe"
private const val FRAGMENT = "Lʽٴ/ᐧᐧ;"
private const val MODEL = "Lʽᐧ/ˉ;"
private const val BRIDGE = "Lapp/morphe/extension/king/MenuBridge;"
private const val LVL_ID = 0x7e4d0001
private const val UI_ID = 0x7e4d0002
private val compatibility = Compatibility(
    name = "King-Patcher", packageName = PACKAGE,
    targets = listOf(AppTarget(version = "12.10.10", minSdk = 23, isExperimental = true))
)

private val kingExtension = bytecodePatch { extendWith("extensions/king.mpe") }

private val menuDispatcher = bytecodePatch {
    dependsOn(kingExtension)
    execute {
        require(packageMetadata.versionName == "12.10.10" && packageMetadata.versionCode == "1980") {
            "Only the inspected King-Patcher 12.10.10 / 1980 is supported"
        }
        val fragment = mutableClassDefBy(FRAGMENT)
        require(fragment.fields.any { it.name == "ʼﹶ" && it.type == "Lru/jgaiecip/osuojvyxe/MainActivity;" &&
            AccessFlags.STATIC.isSet(it.accessFlags) && AccessFlags.PUBLIC.isSet(it.accessFlags) }) {
            "Reviewed King host Activity field not found"
        }
        val dispatch = fragment.methods.singleOrNull { method ->
            method.name == "ˊᵎ" && method.returnType == "V" &&
                method.parameterTypes.map { it.toString() } == listOf("I") && !AccessFlags.STATIC.isSet(method.accessFlags)
        } ?: error("Reviewed King menu dispatcher not found")
        val instructions = requireNotNull(dispatch.implementation).instructions.toList()
        require(dispatch.implementation!!.registerCount == 24 && instructions.size > 500 &&
            instructions[0].opcode == Opcode.MOVE_OBJECT_FROM16 &&
            (instructions[0] as? TwoRegisterInstruction)?.registerA == 1 &&
            (instructions[0] as? TwoRegisterInstruction)?.registerB == 22 &&
            instructions[1].opcode == Opcode.MOVE_FROM16 &&
            (instructions[1] as? TwoRegisterInstruction)?.registerA == 2 &&
            (instructions[1] as? TwoRegisterInstruction)?.registerB == 23
        ) { "Reviewed King dispatcher register layout changed" }
        require(instructions.none { instruction ->
            (instruction as? com.android.tools.smali.dexlib2.iface.instruction.NarrowLiteralInstruction)?.narrowLiteral in setOf(LVL_ID, UI_ID)
        }) { "Experimental menu IDs already in use" }
        dispatch.addInstructionsWithLabels(0, """
            sget-object v0, $FRAGMENT->ʼﹶ:Lru/jgaiecip/osuojvyxe/MainActivity;
            move/from16 v3, p1
            invoke-static {v0, v3}, $BRIDGE->handle(Landroid/app/Activity;I)Z
            move-result v0
            if-eqz v0, :king_original
            return-void
            :king_original
            nop
        """.trimIndent())
    }
}

/** Add one raw-label model item immediately after each reviewed list is constructed. */
private fun app.morphe.patcher.patch.BytecodePatchContext.addMenuItem(id: Int, title: String, description: String) {
    val model = mutableClassDefBy(MODEL)
    require(model.fields.any { it.name == "ʻ" && it.type == "I" } &&
        model.fields.any { it.name == "ʼ" && it.type == "Ljava/lang/String;" } &&
        model.fields.any { it.name == "ʿ" && it.type == "Ljava/lang/String;" }
    ) { "Reviewed King menu fields changed" }
    val rawConstructor = model.methods.singleOrNull { method -> method.name == "<init>" && method.returnType == "V" &&
        method.parameterTypes.map { it.toString() } == listOf("I", "Ljava/lang/String;", "I", "Ljava/lang/String;", "Ljava/lang/String;", "I")
    } ?: error("Reviewed raw-label menu constructor missing")
    val constructorBody = requireNotNull(rawConstructor.implementation)
    fun assignsString(field: String, from: Int) = constructorBody.instructions.any { instruction ->
        val registers = instruction as? TwoRegisterInstruction
        val ref = (instruction as? ReferenceInstruction)?.reference as? FieldReference
        instruction.opcode == Opcode.IPUT_OBJECT && registers?.registerA == from && registers.registerB == 3 &&
            ref?.definingClass == MODEL && ref.name == field && ref.type == "Ljava/lang/String;"
    }
    require(constructorBody.registerCount == 10 && assignsString("ʼ", 5) && assignsString("ʿ", 8)) {
        "Reviewed title or color constructor semantics changed"
    }
    val fragment = mutableClassDefBy(FRAGMENT)
    for ((name, listRegister, startRegister, expectedRegisters) in listOf(
        MenuSpec("ˆʻ", 0, 1, 14), MenuSpec("ˆˎ", 2, 3, 15)
    )) {
        val method = fragment.methods.singleOrNull { it.name == name && it.returnType == "V" && it.parameterTypes.isEmpty() && !AccessFlags.STATIC.isSet(it.accessFlags) }
            ?: error("Reviewed King list builder $name not found")
        val implementation = requireNotNull(method.implementation)
        val instructions = implementation.instructions.toList()
        require(implementation.registerCount == expectedRegisters && instructions.size > 50) { "Reviewed menu registers changed" }
        val constructors = instructions.indices.filter { index ->
            val instruction = instructions[index]
            val ref = (instruction as? ReferenceInstruction)?.reference as? MethodReference
            instruction.opcode == Opcode.INVOKE_DIRECT && ref?.definingClass == "Ljava/util/ArrayList;" &&
                ref.name == "<init>" && ref.parameterTypes.isEmpty() &&
                (instruction as? FiveRegisterInstruction)?.registerCount == 1 &&
                (instruction as? FiveRegisterInstruction)?.registerC == listRegister
        }
        require(constructors.size == 1 && constructors[0] > 0) { "Reviewed menu list initialization changed" }
        val init = constructors[0]
        val allocation = instructions[init - 1]
        require(allocation.opcode == Opcode.NEW_INSTANCE && (allocation as? OneRegisterInstruction)?.registerA == listRegister &&
            ((allocation as? ReferenceInstruction)?.reference as? TypeReference)?.type == "Ljava/util/ArrayList;") {
            "Reviewed menu allocation changed"
        }
        val v = startRegister
        // The fifth argument is parsed as an Android color by King's renderer.
        // Scratch registers are uninitialized at this point; the original code assigns them before use.
        method.addInstructions(init + 1, """
            new-instance v$v, $MODEL
            const v${v + 1}, 0x${id.toString(16)}
            const-string v${v + 2}, "$title"
            const/4 v${v + 3}, 0x0
            const-string v${v + 4}, "$description"
            const-string v${v + 5}, "#FFFFFF"
            const v${v + 6}, 0x7f080083
            invoke-direct/range {v$v .. v${v + 6}}, $MODEL-><init>(ILjava/lang/String;ILjava/lang/String;Ljava/lang/String;I)V
            invoke-virtual {v$listRegister, v$v}, Ljava/util/ArrayList;->add(Ljava/lang/Object;)Z
        """.trimIndent())
    }
}
private data class MenuSpec(val name: String, val list: Int, val scratch: Int, val registers: Int)

@Suppress("unused")
val newPlayLvlPatch = bytecodePatch(
    name = "Remove license (new Google Play LVL method)",
    description = "Add an automatic on-device license-check scanner to King-Patcher. Supports only classic unobfuscated Google Play LVL and the reviewed PairIP client pattern; other checks may remain. Selected single APKs only; output is separately signed. Experimental.",
    default = false,
) {
    compatibleWith(compatibility)
    dependsOn(menuDispatcher)
    execute { addMenuItem(LVL_ID, "Remove license check (automatic)", "Scan for supported LVL and PairIP checks") }
}

@Suppress("unused")
val removeUiElementsPatch = bytecodePatch(
    name = "Remove insignificant things (manual UI selection)",
    description = "Add a King-Patcher menu entry to select and hide elements in compiled Android layouts of a selected single APK. Runtime-generated, Compose and WebView UI are not supported. The output is separately signed. Experimental and not yet device-verified.",
    default = false,
) {
    compatibleWith(compatibility)
    dependsOn(menuDispatcher)
    execute { addMenuItem(UI_ID, "Remove insignificant things", "Choose compiled layout elements to hide") }
}
