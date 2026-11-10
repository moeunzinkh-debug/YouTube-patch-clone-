package app.morphe.patches.simsimi

import app.morphe.patcher.extensions.InstructionExtensions.addInstruction
import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.bytecodePatch
import com.android.tools.smali.dexlib2.AccessFlags
import com.android.tools.smali.dexlib2.iface.instruction.ReferenceInstruction
import com.android.tools.smali.dexlib2.iface.reference.MethodReference

private const val BOTTOM_BAR_923 = "Lcom/aurelhubert/ahbottomnavigation/i;"
private const val BOTTOM_BAR_926 = "Lcom/aurelhubert/ahbottomnavigation/a;"
private const val QUICK_RETURN = "Lapp/morphe/extension/simsimi/QuickReturn;"

@Suppress("unused")
val quickReturnPatch = bytecodePatch(
    name = "Quick return: double-tap Chat (experimental)",
    description = "Double-tap the already-selected Chat tab to scroll the English Conversation list to the top. Does not reload the app, consume the original tap, or scroll inside a chat room. Uses separately verified native click targets for SimSimi 9.2.3 and 9.2.6; device runtime testing is still required.",
    default = false
) {
    compatibleWith(Compatibility(
        name = "SimSimi", packageName = "com.ismaker.android.simsimi",
        targets = listOf(
            AppTarget(version = "9.2.3", minSdk = 24, isExperimental = true),
            AppTarget(version = "9.2.6", minSdk = 24, isExperimental = true)
        )
    ))
    dependsOn(simSimiExtensionPatch)
    execute {
        check(packageMetadata.versionName in setOf("9.2.3", "9.2.6")) {
            "Quick return supports only SimSimi 9.2.3 and 9.2.6"
        }
        val is926 = packageMetadata.versionName == "9.2.6"
        val bottomBar = if (is926) BOTTOM_BAR_926 else BOTTOM_BAR_923
        val bridgeNames = if (is926) setOf("a", "b") else setOf("b", "f")
        val listenerOwners = if (is926) {
            setOf("Lcom/reactnativenavigation/customrow/d;", "Le6/a;")
        } else {
            setOf("Lcom/aurelhubert/ahbottomnavigation/a;", "Lcom/aurelhubert/ahbottomnavigation/b;")
        }
        val bar = mutableClassDefBy(bottomBar)
        require(bar.superclass == "Landroid/widget/FrameLayout;") { "Unsupported bottom navigation class" }
        require(bar.methods.any {
            it.name == "getCurrentItem" && it.parameterTypes.isEmpty() && it.returnType == "I" &&
                AccessFlags.PUBLIC.isSet(it.accessFlags)
        }) { "Current bottom-tab selection is unavailable" }

        // Verify that these paths are real View.OnClickListener dispatch, not programmatic setCurrentItem.
        val clickHandlers = mapOf(
            "lambda\$createClassicItems\$5" to "updateItems",
            "lambda\$createSmallItems\$6" to "updateSmallItems"
        )
        val bridgeTargets = bar.methods.filter { method ->
            method.name in bridgeNames && AccessFlags.STATIC.isSet(method.accessFlags) &&
                method.parameterTypes.map { it.toString() } == listOf(bottomBar, "I", "Landroid/view/View;") && method.returnType == "V"
        }.flatMap { method ->
            requireNotNull(method.implementation).instructions.mapNotNull { (it as? ReferenceInstruction)?.reference as? MethodReference }
        }.filter { it.definingClass == bottomBar && it.name in clickHandlers.keys }.map { it.name }.toSet()
        require(bridgeTargets == clickHandlers.keys) { "Bottom-tab click listener bridges do not match" }
        val listenerBridges = listenerOwners.map { owner ->
            val listener = mutableClassDefBy(owner)
            require("Landroid/view/View\$OnClickListener;" in listener.interfaces) { "Bottom-tab listener interface missing" }
            val callback = listener.methods.single { it.name == "onClick" && it.parameterTypes.map { type -> type.toString() } == listOf("Landroid/view/View;") && it.returnType == "V" }
            requireNotNull(callback.implementation).instructions.mapNotNull { (it as? ReferenceInstruction)?.reference as? MethodReference }
                .single { it.definingClass == bottomBar && it.name in bridgeNames }.name
        }.toSet()
        require(listenerBridges == bridgeNames) { "Bottom-tab click dispatch does not match" }

        clickHandlers.forEach { (name, originalUpdate) ->
            val handler = bar.methods.singleOrNull { method ->
                method.name == name && method.returnType == "V" &&
                    method.parameterTypes.map { it.toString() } == listOf("I", "Landroid/view/View;")
            } ?: error("Unsupported bottom-tab click handler: $name")
            require(AccessFlags.PRIVATE.isSet(handler.accessFlags) && AccessFlags.SYNTHETIC.isSet(handler.accessFlags)) {
                "Bottom-tab click handler access changed: $name"
            }
            val implementation = requireNotNull(handler.implementation) { "Bottom-tab click handler has no code" }
            require(implementation.registerCount in 3..16) { "Unsupported bottom-tab click register layout" }
            val refs = implementation.instructions.mapNotNull { (it as? ReferenceInstruction)?.reference as? MethodReference }
            require(refs.any {
                it.definingClass == bottomBar && it.name == originalUpdate &&
                    it.parameterTypes.map { type -> type.toString() } == listOf("I", "Z") && it.returnType == "V"
            }) { "Bottom-tab click update path changed: $name" }
            require(refs.none { it.definingClass == QUICK_RETURN }) { "Quick return hook is already installed" }
            handler.addInstruction(0, "invoke-static {p0, p1}, $QUICK_RETURN->onTabClicked(Landroid/view/View;I)V")
        }
    }
}
