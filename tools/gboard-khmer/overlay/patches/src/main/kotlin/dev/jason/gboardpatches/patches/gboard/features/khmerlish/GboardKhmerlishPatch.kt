/* Copyright (C) 2026. This fork is distributed under GPL-3.0-or-later. */
package dev.jason.gboardpatches.patches.gboard.features.khmerlish

import app.morphe.patcher.extensions.InstructionExtensions.addInstructions
import app.morphe.patcher.patch.ResourcePatchContext
import app.morphe.patcher.patch.bytecodePatch
import app.morphe.patcher.patch.resourcePatch
import app.morphe.patcher.resource.PublicXmlManager
import com.android.tools.smali.dexlib2.iface.instruction.FiveRegisterInstruction
import dev.jason.gboardpatches.patches.gboard.features.featureflags.applyFeatureMarker
import dev.jason.gboardpatches.patches.gboard.shared.accesspoint.GboardAccessPointContributionsTargets
import dev.jason.gboardpatches.patches.gboard.shared.accesspoint.gboardAccessPointContributions1803Patch
import dev.jason.gboardpatches.patches.gboard.shared.findMutableMethodOrThrow
import dev.jason.gboardpatches.patches.gboard.shared.gboardPatchesSettingsPatch
import dev.jason.gboardpatches.patches.gboard.shared.isMethodReference
import dev.jason.gboardpatches.patches.gboard.shared.isOpcode
import dev.jason.gboardpatches.patches.gboard.shared.mutableClass
import dev.jason.gboardpatches.patches.gboard.shared.returnInstructionIndices
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
    val iconName = "gboard_khmerlish_panel"
    val iconBytes = loader.getResourceAsStream("$RESOURCE_ROOT/$iconName.xml")?.use { it.readBytes() }
        ?: error("Missing Khmerlish toolbar icon")
    val icon = this["res/drawable/$iconName.xml", false]
    check(!icon.isFile || icon.readBytes().contentEquals(iconBytes)) {
        "Khmerlish toolbar drawable collides with an existing resource"
    }
    icon.parentFile?.mkdirs()
    icon.writeBytes(iconBytes)
    PublicXmlManager(this["res/values/public.xml"]).use { publicIds ->
        publicIds.createPublicId("drawable", iconName)
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
    description = "Adds an offline Khmerlish toolbar panel and an optional automatic setting. " +
        "Known Romanized words are converted to Khmer; unknown and ambiguous spellings stay unchanged.",
    default = false,
) {
    compatibleWith(COMPATIBILITY_GBOARD)
    dependsOn(
        gboardPatchesSettingsPatch, gboardKhmerlishMarkerPatch, gboardKhmerlishAssetsPatch,
        gboardAccessPointContributions1803Patch,
    )

    execute {
        check(packageMetadata.versionName == "18.5.4.993608717-release-arm64-v8a" &&
            packageMetadata.versionCode == "176049702") {
            "Khmerlish supports only the reviewed Gboard 18.5.4 version and code"
        }
        check(mutableClass("Lphr;").superclass == "Landroid/inputmethodservice/InputMethodService;") {
            "Gboard input service changed"
        }
        // Keep our delegate separate from the shared extension class. This also
        // works when a disposable, already-patched fixture retains older shared
        // extension methods during class merging.
        val catalog = findMutableMethodOrThrow(GboardAccessPointContributionsTargets.orderFactory)
        val controller = findMutableMethodOrThrow(GboardAccessPointContributionsTargets.controllerConstructor)
        val catalogRef = RuntimeAbiCatalog.abi(RuntimeCallId.KHMERLISH_ACCESS_POINT_CATALOG).reference
        val registerRef = RuntimeAbiCatalog.abi(RuntimeCallId.KHMERLISH_ACCESS_POINT_REGISTER).reference
        check(catalog.implementation?.instructions?.none { it.isMethodReference(catalogRef) } == true)
        check(controller.implementation?.instructions?.none { it.isMethodReference(registerRef) } == true)
        catalog.addInstructions(
            0,
            """
                move-object/from16 v0, p0
                move-object/from16 v1, p3
                ${RuntimeCallEmitter.invoke(RuntimeCallId.KHMERLISH_ACCESS_POINT_CATALOG, "v0, v1")}
                move-result-object v0
                move-object/from16 p3, v0
                check-cast p3, Lwpa;
            """.trimIndent(),
        )
        val constructorReturns = controller.returnInstructionIndices().filter {
            controller.implementation!!.instructions[it].isOpcode("RETURN_VOID")
        }
        check(constructorReturns.size == 1) { "Unexpected Gboard toolbar controller constructor" }
        controller.addInstructions(constructorReturns.single(), RuntimeCallEmitter.invoke(
            RuntimeCallId.KHMERLISH_ACCESS_POINT_REGISTER, "p0, p1",
        ))
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
