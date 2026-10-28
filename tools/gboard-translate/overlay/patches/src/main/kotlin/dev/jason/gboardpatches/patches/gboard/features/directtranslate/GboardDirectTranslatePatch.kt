/* Copyright (C) 2026. This fork is distributed under GPL-3.0-or-later. */
package dev.jason.gboardpatches.patches.gboard.features.directtranslate

import app.morphe.patcher.extensions.InstructionExtensions.addInstructions
import app.morphe.patcher.extensions.InstructionExtensions.addInstructionsWithLabels
import app.morphe.patcher.patch.bytecodePatch
import app.morphe.patcher.util.proxy.mutableTypes.MutableMethod
import app.morphe.patcher.util.smali.ExternalLabel
import com.android.tools.smali.dexlib2.iface.instruction.FiveRegisterInstruction
import dev.jason.gboardpatches.patches.gboard.shared.findMutableMethodOrThrow
import dev.jason.gboardpatches.patches.gboard.shared.gboardPatchesExtensionCarrierPatch
import dev.jason.gboardpatches.patches.gboard.shared.isMethodReference
import dev.jason.gboardpatches.patches.gboard.shared.mutableClass
import dev.jason.gboardpatches.patches.gboard.shared.runtimeabi.RuntimeAbiCatalog
import dev.jason.gboardpatches.patches.gboard.shared.runtimeabi.RuntimeCallEmitter
import dev.jason.gboardpatches.patches.gboard.shared.runtimeabi.RuntimeCallId
import dev.jason.gboardpatches.patches.shared.Constants.COMPATIBILITY_GBOARD

/** Experimental, opt-in and deliberately restricted to the reviewed version. */
internal val gboardDirectGoogleTranslatePatch = bytecodePatch(
    name = "Direct Google Translate (experimental)",
    description = "Sends native Translate input directly to Google's unofficial GTX endpoint. " +
        "May override Android offline translation for this UI. Requires internet; may stop working.",
    default = false,
) {
    compatibleWith(COMPATIBILITY_GBOARD)
    dependsOn(gboardPatchesExtensionCarrierPatch)

    execute {
        check(packageMetadata.versionName == "18.5.4.993608717-release-arm64-v8a" &&
            packageMetadata.versionCode == "176049702") {
            "Direct Google Translate supports only the reviewed Gboard 18.5.4 version and code"
        }
        check(mutableClass("Lkjx;").superclass == "Lkkp;") { "Google provider changed" }
        fun field(owner: String, name: String, type: String) {
            check(mutableClass(owner).fields.count { it.name == name && it.type == type } == 1) {
                "Native Translate field changed: $owner->$name"
            }
        }
        field("Lklg;", "a", "Ljava/lang/String;")
        field("Lklg;", "b", "Ljava/lang/String;")
        field("Lklg;", "c", "Ljava/lang/String;")
        field("Labxb;", "a", "Ljava/lang/Object;")
        field("Lklo;", "p", "Lkkd;")
        field("Lklo;", "u", "Lkko;")
        field("Lkko;", "c", "Z")
        field("Lkka;", "f", "Lkkd;")
        findMutableMethodOrThrow("Labxb;", "<init>", "V", listOf("Ljava/lang/String;"))
        findMutableMethodOrThrow("Labxb;", "<init>", "V", listOf("I"))
        findMutableMethodOrThrow("Lkli;", "a", "V", listOf("Labxb;"))

        val dispatch = findMutableMethodOrThrow("Lkkp;", "e", "V", listOf("Lklg;", "Lkkc;"))
        val wrapper = findMutableMethodOrThrow("Lkka;", "d", "V", listOf("Lklg;", "Lkkc;"))
        val ready = findMutableMethodOrThrow("Lklo;", "ap", "Z", emptyList())
        val input = findMutableMethodOrThrow("Lklo;", "al", "V", listOf("Ljava/lang/String;"))
        val inputStarted = findMutableMethodOrThrow("Lklo;", "fL", "V", emptyList())
        val close = findMutableMethodOrThrow("Lklo;", "fN", "V", emptyList())
        val finishView = findMutableMethodOrThrow("Lphr;", "onFinishInputView", "V", listOf("Z"))
        val finishInput = findMutableMethodOrThrow("Lphr;", "onFinishInput", "V", emptyList())
        val windowHidden = findMutableMethodOrThrow("Lphr;", "onWindowHidden", "V", emptyList())
        check(mutableClass("Lphr;").superclass == "Landroid/inputmethodservice/InputMethodService;") {
            "Keyboard lifecycle owner changed"
        }
        dispatch.requireStock(5, "Lkkp;->a(Lklg;)Lxqp;")
        wrapper.requireStock(6, "Lkka;->e(Lklg;Lkkc;)V")
        ready.requireStock(5, "Lkko;->a(I)I")
        input.requireStock(10, "Lkkd;->d(Lklg;Lkkc;)V")
        listOf(inputStarted, close, finishView, finishInput, windowHidden).forEach {
            check(it.implementation != null) { "Missing native Translate lifecycle body" }
        }
        val runtimeReferences = listOf(
            RuntimeCallId.DIRECT_TRANSLATE_TRY_DISPATCH,
            RuntimeCallId.DIRECT_TRANSLATE_PREPARE,
            RuntimeCallId.DIRECT_TRANSLATE_CANCEL,
        ).map { RuntimeAbiCatalog.abi(it).reference }
        listOf(dispatch, wrapper, ready, input, inputStarted, close, finishView, finishInput, windowHidden)
            .forEach { method ->
                check(method.implementation!!.instructions.none { instruction ->
                    runtimeReferences.any { reference -> instruction.isMethodReference(reference) }
                }) { "Direct Translate is already applied or the native method has drifted" }
            }
        val inputInvokeIndex = input.implementation!!.instructions.indexOfFirst {
            it.isMethodReference("Lkkd;->d(Lklg;Lkkc;)V")
        }
        val inputInvoke = input.implementation!!.instructions[inputInvokeIndex] as? FiveRegisterInstruction
            ?: error("Native Translate request dispatch instruction changed")
        check(inputInvoke.registerCount == 3) { "Unexpected native Translate dispatch registers" }
        val requestRegister = inputInvoke.registerD
        val callbackRegister = inputInvoke.registerE

        // Keep Gboard's throttle and all non-UI/health callbacks. The Java
        // bridge additionally checks the exact native provider and callback.
        dispatch.addInstructions(0, "nop")
        val originalDispatch = dispatch.implementation!!.instructions[0]
        dispatch.addInstructionsWithLabels(
            0,
            """
            ${RuntimeCallEmitter.invoke(RuntimeCallId.DIRECT_TRANSLATE_TRY_DISPATCH, "p0 .. p2")}
            move-result v0
            if-eqz v0, :original_dispatch
            return-void
            """,
            ExternalLabel("original_dispatch", originalDispatch),
        )

        // On Android 12+ the native wrapper may prefer a system/offline
        // provider. Override only the user-facing UI callback and only when
        // its cloud provider is the reviewed Google implementation.
        wrapper.addInstructions(0, "nop")
        val originalWrapper = wrapper.implementation!!.instructions[0]
        wrapper.addInstructionsWithLabels(
            0,
            """
            instance-of v0, p2, Lkli;
            if-eqz v0, :original_wrapper
            iget-object v0, p0, Lkka;->f:Lkkd;
            instance-of v1, v0, Lkjx;
            if-eqz v1, :original_wrapper
            invoke-interface {v0, p1, p2}, Lkkd;->d(Lklg;Lkkc;)V
            return-void
            """,
            ExternalLabel("original_wrapper", originalWrapper),
        )

        // Permit dispatch despite a failed cloud health probe, but only for
        // the exact cloud provider (directly or behind the native wrapper).
        ready.addInstructions(0, "nop")
        val originalReady = ready.implementation!!.instructions[0]
        ready.addInstructionsWithLabels(
            0,
            """
            iget-object v0, p0, Lklo;->u:Lkko;
            if-eqz v0, :original_ready
            iget-boolean v1, v0, Lkko;->c:Z
            if-nez v1, :original_ready
            iget-object v0, p0, Lklo;->p:Lkkd;
            instance-of v1, v0, Lkjx;
            if-nez v1, :direct_ready
            instance-of v1, v0, Lkka;
            if-eqz v1, :original_ready
            check-cast v0, Lkka;
            iget-object v0, v0, Lkka;->f:Lkkd;
            instance-of v1, v0, Lkjx;
            if-eqz v1, :original_ready
            :direct_ready
            const/4 v0, 0x1
            return v0
            """,
            ExternalLabel("original_ready", originalReady),
        )

        // Record the exact native request/callback pair immediately before
        // Gboard queues it. A delayed native throttle callback arriving after
        // a later edit or keyboard close must not initiate a new HTTP request.
        input.addInstructions(
            inputInvokeIndex,
            RuntimeCallEmitter.invoke(
                RuntimeCallId.DIRECT_TRANSLATE_PREPARE,
                "v$requestRegister, v$callbackRegister",
            ),
        )
        val cancel = RuntimeCallEmitter.invoke(RuntimeCallId.DIRECT_TRANSLATE_CANCEL, "")
        // Invalidate even an empty edit before the next throttled request, so
        // an older HTTP result cannot overwrite newer input or a closed view.
        listOf(input, inputStarted, close, finishView, finishInput, windowHidden).forEach {
            it.addInstructions(0, cancel)
        }
    }
}

private fun MutableMethod.requireStock(registers: Int, reference: String) {
    val body = implementation ?: error("Missing native Translate method body")
    check(body.registerCount == registers && body.instructions.count { it.isMethodReference(reference) } == 1) {
        "Native Translate fingerprint mismatch: $definingClass->$name"
    }
}
