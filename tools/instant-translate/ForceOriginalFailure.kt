// CI-ONLY FAULT INJECTION. This file is never included in the distributed MPP.
// It forces the original single-result engine to return null in a disposable
// emulator, so the genuine fallback hook can be exercised with a synthetic word.
package app.morphe.patches.instanttranslatetest

import app.morphe.patcher.extensions.InstructionExtensions.addInstructions
import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.bytecodePatch
import com.android.tools.smali.dexlib2.AccessFlags

@Suppress("unused")
val ciForceOriginalFailure = bytecodePatch(
    name = "CI only: force original translation failure",
    description = "Test-only fault injection. Never distribute or use on a real device.",
    default = false,
) {
    compatibleWith(Compatibility(
        name = "Instant Translate", packageName = "com.spaceship.screen.textcopy",
        targets = listOf(AppTarget(version = "v7.5.00300", minSdk = 29, isExperimental = true)),
    ))
    execute {
        require(packageMetadata.versionName == "v7.5.00300" && packageMetadata.versionCode == "50342")
        val method = mutableClassDefBy("Lus9;").methods.singleOrNull {
            it.name == "G" && it.returnType == "Ljava/lang/Object;" &&
                it.parameterTypes.map { p -> p.toString() } == listOf("Lmx1;") &&
                !AccessFlags.STATIC.isSet(it.accessFlags)
        } ?: error("CI-only native translator method did not match")
        requireNotNull(method.implementation)
        // The original suspend method normally returns a nullable String (or
        // COROUTINE_SUSPENDED); null triggers the tested caller's failure path.
        method.addInstructions(0, """
            const/4 v0, 0x0
            return-object v0
        """.trimIndent())
    }
}
