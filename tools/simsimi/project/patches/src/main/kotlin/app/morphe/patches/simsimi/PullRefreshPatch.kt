package app.morphe.patches.simsimi

import app.morphe.patcher.extensions.InstructionExtensions.addInstructions
import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.bytecodePatch
import app.morphe.patcher.util.proxy.mutableTypes.MutableMethod.Companion.toMutable
import com.android.tools.smali.dexlib2.AccessFlags
import com.android.tools.smali.dexlib2.builder.MutableMethodImplementation
import com.android.tools.smali.dexlib2.immutable.ImmutableMethod
import com.android.tools.smali.dexlib2.immutable.ImmutableMethodParameter

@Suppress("unused")
val pullRefreshPatch = bytecodePatch(
    name = "Pull down to restart chat (experimental)",
    description = "Pull down at least 160dp from the top 96dp to request a React chat/home reload. Does not kill the app. Skips focused text input and scrolled content. Reload can discard unsaved screen state; device testing required."
) {
    compatibleWith(Compatibility(
        name = "SimSimi", packageName = "com.ismaker.android.simsimi",
        targets = listOf(AppTarget(version = "9.2.3", minSdk = 24, isExperimental = true))
    ))
    extendWith("extensions/simsimi.mpe")
    execute {
        val activity = mutableClassDefBy("Lcom/ismaker/android/simsimi/MainActivity;")
        require(activity.superclass == "Lcom/reactnativenavigation/NavigationActivity;") { "Unsupported SimSimi activity base" }
        require(activity.methods.none { it.name == "dispatchTouchEvent" }) { "Touch dispatch already customized; refusing to overwrite" }
        val bridge = ImmutableMethod(
            activity.type, "dispatchTouchEvent",
            listOf(ImmutableMethodParameter("Landroid/view/MotionEvent;", null, null)),
            "Z", AccessFlags.PUBLIC.value, null, null, MutableMethodImplementation(3)
        ).toMutable()
        bridge.addInstructions(0, """
            invoke-static {p0, p1}, Lapp/morphe/extension/simsimi/PullRefresh;->onTouch(Landroid/app/Activity;Landroid/view/MotionEvent;)V
            invoke-super {p0, p1}, Lcom/reactnativenavigation/NavigationActivity;->dispatchTouchEvent(Landroid/view/MotionEvent;)Z
            move-result v0
            return v0
        """.trimIndent())
        activity.methods.add(bridge)
    }
}
