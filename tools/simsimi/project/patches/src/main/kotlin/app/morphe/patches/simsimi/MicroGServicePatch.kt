package app.morphe.patches.simsimi

import app.morphe.patcher.extensions.InstructionExtensions.replaceInstruction
import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.bytecodePatch
import app.morphe.patcher.patch.resourcePatch
import com.android.tools.smali.dexlib2.Opcode
import com.android.tools.smali.dexlib2.iface.instruction.OneRegisterInstruction
import com.android.tools.smali.dexlib2.iface.instruction.ReferenceInstruction
import com.android.tools.smali.dexlib2.iface.reference.StringReference

private const val RE_PACKAGE = "app.revanced.android.gms"
private const val RE_PERMISSION = "$RE_PACKAGE.EXTENDED_ACCESS"
private val microGVisibilityPatch = resourcePatch {
    execute {
        document("AndroidManifest.xml").use { doc ->
            val root = doc.documentElement
            val permissions = doc.getElementsByTagName("uses-permission")
            if ((0 until permissions.length).none { (permissions.item(it) as org.w3c.dom.Element).getAttribute("android:name") == RE_PERMISSION }) {
                root.appendChild(doc.createElement("uses-permission").apply { setAttribute("android:name", RE_PERMISSION) })
            }
            val queries = doc.getElementsByTagName("queries").item(0)
                ?: doc.createElement("queries").also { root.appendChild(it) }
            val packages = (queries as org.w3c.dom.Element).getElementsByTagName("package")
            if ((0 until packages.length).none { (packages.item(it) as org.w3c.dom.Element).getAttribute("android:name") == RE_PACKAGE }) {
                queries.appendChild(doc.createElement("package").apply { setAttribute("android:name", RE_PACKAGE) })
            }
        }
    }
}

/** Service-package routing, not a fabricated success result for missing GMS APIs. */
@Suppress("unused")
val microGServicePatch = bytecodePatch(
    name = "MicroG RE service routing (experimental)",
    description = "Routes exact native Google service package references to app.revanced.android.gms and adds visibility/extended-access permission. Requires matching MicroG RE installed. Does not emulate Play Billing or bypass Firebase App Check, signatures, attestation or unsupported APIs; compatibility is not yet device-verified.",
    default = false
) {
    compatibleWith(Compatibility(
        name = "SimSimi", packageName = "com.ismaker.android.simsimi",
        targets = listOf(AppTarget(version = "9.2.3", minSdk = 24, isExperimental = true))
    ))
    dependsOn(microGVisibilityPatch)
    execute {
        var replacements = 0
        classDefByStrings("com.google.android.gms").forEach { clazz ->
            clazz.methods.forEach methodLoop@ { original ->
                val instructions = original.implementation?.instructions?.toList() ?: return@methodLoop
                val indices = instructions.withIndex().filter { (_, instruction) ->
                    (instruction.opcode == Opcode.CONST_STRING || instruction.opcode == Opcode.CONST_STRING_JUMBO) &&
                        ((instruction as? ReferenceInstruction)?.reference as? StringReference)?.string == "com.google.android.gms"
                }
                if (indices.isEmpty()) return@methodLoop
                val mutable = mutableClassDefBy(clazz).methods.first {
                    it.name == original.name && it.returnType == original.returnType &&
                        it.parameterTypes.map { type -> type.toString() } == original.parameterTypes.map { type -> type.toString() }
                }
                indices.forEach { (index, instruction) ->
                    val register = (instruction as OneRegisterInstruction).registerA
                    mutable.replaceInstruction(index, "const-string v$register, \"$RE_PACKAGE\"")
                    replacements++
                }
            }
        }
        require(replacements > 0) { "No exact GMS package call sites found; refusing an empty compatibility patch" }
    }
}
