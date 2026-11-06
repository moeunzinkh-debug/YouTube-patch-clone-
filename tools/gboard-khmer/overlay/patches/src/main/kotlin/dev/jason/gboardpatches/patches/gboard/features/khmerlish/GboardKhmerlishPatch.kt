/* Copyright (C) 2026. This fork is distributed under GPL-3.0-or-later. */
package dev.jason.gboardpatches.patches.gboard.features.khmerlish

import app.morphe.patcher.extensions.InstructionExtensions.addInstructions
import app.morphe.patcher.patch.ResourcePatchContext
import app.morphe.patcher.patch.bytecodePatch
import app.morphe.patcher.patch.resourcePatch
import com.android.tools.smali.dexlib2.iface.instruction.FiveRegisterInstruction
import dev.jason.gboardpatches.patches.gboard.features.featureflags.applyFeatureMarker
import dev.jason.gboardpatches.patches.gboard.shared.findMutableMethodOrThrow
import dev.jason.gboardpatches.patches.gboard.shared.gboardPatchesSettingsPatch
import dev.jason.gboardpatches.patches.gboard.shared.isMethodReference
import dev.jason.gboardpatches.patches.gboard.shared.mutableClass
import dev.jason.gboardpatches.patches.gboard.shared.runtimeabi.RuntimeAbiCatalog
import dev.jason.gboardpatches.patches.gboard.shared.runtimeabi.RuntimeCallEmitter
import dev.jason.gboardpatches.patches.gboard.shared.runtimeabi.RuntimeCallId
import dev.jason.gboardpatches.patches.shared.Constants.COMPATIBILITY_GBOARD

private const val FEATURE_MARKER = "dev.jason.gboardpatches.feature.khmerlish"
private const val RESOURCE_ROOT = "gboard-khmer"

private val gboardKhmerlishAssetsPatch = resourcePatch(
    description = "Copy the attributed offline Khmerlish dictionary into the target APK.",
) {
    compatibleWith(COMPATIBILITY_GBOARD)
    finalize { copyKhmerlishAssets() }
}

context(context: ResourcePatchContext)
private fun copyKhmerlishAssets() = with(context) {
    val loader = object {}.javaClass.classLoader
    listOf("dictionary.tsv", "LICENSE.txt").forEach { name ->
        val bytes = loader.getResourceAsStream("$RESOURCE_ROOT/$name")?.use { it.readBytes() }
            ?: error("Missing Khmerlish dictionary resource: $name")
        val target = this["assets/$RESOURCE_ROOT/$name", false]
        target.parentFile?.mkdirs()
        target.outputStream().use { it.write(bytes) }
    }
}

private val gboardKhmerlishMarkerPatch = resourcePatch(
    description = "Mark Khmerlish as available in Gboard Patches settings.",
) {
    compatibleWith(COMPATIBILITY_GBOARD)
    finalize { applyFeatureMarker(FEATURE_MARKER) }
}

/** Explicitly opt-in; exact obfuscated lifecycle targets are reviewed only for this APK version. */
internal val gboardKhmerlishPatch = bytecodePatch(
    name = "Khmerlish to Khmer (experimental)",
    description = "Adds an opt-in offline Khmerlish-to-Khmer setting. Recognized words " +
        "are replaced after a space or punctuation; unknown and ambiguous words are left unchanged.",
    default = false,
) {
    compatibleWith(COMPATIBILITY_GBOARD)
    dependsOn(gboardPatchesSettingsPatch, gboardKhmerlishMarkerPatch, gboardKhmerlishAssetsPatch)

    execute {
        check(packageMetadata.versionName == "18.5.4.993608717-release-arm64-v8a" &&
            packageMetadata.versionCode == "176049702") {
            "Khmerlish supports only the reviewed Gboard 18.5.4 version and code"
        }
        check(mutableClass("Lphr;").superclass == "Landroid/inputmethodservice/InputMethodService;") {
            "Gboard input service changed"
        }
        val selection = findMutableMethodOrThrow(
            "Lphr;", "onUpdateSelection", "V", listOf("I", "I", "I", "I", "I", "I"),
        )
        val start = findMutableMethodOrThrow(
            "Lphr;", "onStartInputView", "V", listOf("Landroid/view/inputmethod/EditorInfo;", "Z"),
        )
        val startInput = findMutableMethodOrThrow(
            "Lphr;", "onStartInput", "V", listOf("Landroid/view/inputmethod/EditorInfo;", "Z"),
        )
        val finish = findMutableMethodOrThrow("Lphr;", "onFinishInput", "V", emptyList())
        val hidden = findMutableMethodOrThrow("Lphr;", "onWindowHidden", "V", emptyList())
        check(selection.implementation?.registerCount == 8) {
            "Gboard selection callback register layout changed"
        }
        // Attach to the existing Patches settings registry instead of replacing
        // a shared extension class. This also preserves the UI in older, already
        // patched test fixtures where the class merger keeps original methods.
        val registry = findMutableMethodOrThrow(
            "Ldev/jason/gboardpatches/extension/settings/GboardPatchesSettingsFeatureRegistry;",
            "features", "Ljava/util/List;", listOf("Landroid/content/Context;"),
        )
        val registryBody = registry.implementation ?: error("Missing Patches settings registry")
        check(registryBody.registerCount == 3) { "Patches settings registry layout changed" }
        val registrySites = registryBody.instructions.withIndex().filter { (_, instruction) ->
            instruction.isMethodReference("Ljava/util/Collections;->unmodifiableList(Ljava/util/List;)Ljava/util/List;")
        }
        check(registrySites.size == 1) { "Expected exactly one settings list finalizer" }
        val listInvoke = registrySites.single().value as? FiveRegisterInstruction
            ?: error("Unexpected settings list finalizer instruction")
        check(listInvoke.registerCount == 1 && listInvoke.registerC == 0) {
            "Unexpected settings list register"
        }
        val settingsCall = RuntimeAbiCatalog.abi(RuntimeCallId.KHMERLISH_ADD_SETTINGS).reference
        check(registryBody.instructions.none { it.isMethodReference(settingsCall) }) {
            "Khmerlish settings hook already exists"
        }
        registry.addInstructions(registrySites.single().index, RuntimeCallEmitter.invoke(
            RuntimeCallId.KHMERLISH_ADD_SETTINGS, "p0, v0",
        ))
        listOf(
            selection to RuntimeCallId.KHMERLISH_ON_SELECTION,
            start to RuntimeCallId.KHMERLISH_ON_INPUT_VIEW_STARTED,
            startInput to RuntimeCallId.KHMERLISH_ON_INPUT_VIEW_STARTED,
            finish to RuntimeCallId.KHMERLISH_RESET,
            hidden to RuntimeCallId.KHMERLISH_RESET,
        ).forEach { (method, call) ->
            val body = method.implementation ?: error("Missing Gboard lifecycle body")
            val ref = RuntimeAbiCatalog.abi(call).reference
            check(body.instructions.none { it.isMethodReference(ref) }) {
                "Khmerlish hook already exists in ${method.definingClass}->${method.name}"
            }
        }
        // The callback is posted to the main queue by the extension so the
        // native Gboard lifecycle method can complete before text is replaced.
        selection.addInstructions(0, RuntimeCallEmitter.invoke(
            RuntimeCallId.KHMERLISH_ON_SELECTION, "p0 .. p6",
        ))
        listOf(start, startInput).forEach { method ->
            method.addInstructions(0, RuntimeCallEmitter.invoke(
                RuntimeCallId.KHMERLISH_ON_INPUT_VIEW_STARTED, "p0 .. p0",
            ))
        }
        finish.addInstructions(0, RuntimeCallEmitter.invoke(
            RuntimeCallId.KHMERLISH_RESET, "p0 .. p0",
        ))
        hidden.addInstructions(0, RuntimeCallEmitter.invoke(
            RuntimeCallId.KHMERLISH_RESET, "p0 .. p0",
        ))
    }
}
