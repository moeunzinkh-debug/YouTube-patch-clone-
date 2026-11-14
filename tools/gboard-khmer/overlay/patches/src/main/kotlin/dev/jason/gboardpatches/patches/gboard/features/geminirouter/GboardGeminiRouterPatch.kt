/* Copyright (C) 2026. This fork is distributed under GPL-3.0-or-later. */
package dev.jason.gboardpatches.patches.gboard.features.geminirouter

import app.morphe.patcher.extensions.InstructionExtensions.addInstructions
import app.morphe.patcher.patch.ResourcePatchContext
import app.morphe.patcher.patch.bytecodePatch
import app.morphe.patcher.patch.resourcePatch
import app.morphe.patcher.resource.PublicXmlManager
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

private const val FEATURE_MARKER = "dev.jason.gboardpatches.feature.gemini_router"
private const val RESOURCE_ROOT = "gboard-gemini"
private const val ICON_NAME = "gboard_gemini_chat"

private val gboardGeminiRouterAssetsPatch = resourcePatch(
    description = "Copy the Gmn Gemini router toolbar icon into the target APK.",
) {
    compatibleWith(COMPATIBILITY_GBOARD)
    finalize { copyGeminiRouterIcon() }
}

context(context: ResourcePatchContext)
private fun copyGeminiRouterIcon() = with(context) {
    val bytes = object {}.javaClass.classLoader
        .getResourceAsStream("$RESOURCE_ROOT/$ICON_NAME.xml")?.use { it.readBytes() }
        ?: error("Missing Gmn toolbar icon")
    val icon = this["res/drawable/$ICON_NAME.xml", false]
    check(!icon.isFile || icon.readBytes().contentEquals(bytes)) {
        "Gemini router toolbar drawable collides with an existing resource"
    }
    icon.parentFile?.mkdirs()
    icon.writeBytes(bytes)
    PublicXmlManager(this["res/values/public.xml"]).use { ids ->
        ids.createPublicId("drawable", ICON_NAME)
    }
}

private val gboardGeminiRouterMarkerPatch = resourcePatch(
    description = "Mark the Gemini chat router as available in the patched Gboard APK.",
) {
    compatibleWith(COMPATIBILITY_GBOARD)
    finalize { applyFeatureMarker(FEATURE_MARKER) }
}

/** Opt-in Gmn toolbar route. It never embeds credentials or calls an unofficial Gemini API. */
internal val gboardGeminiChatRouterPatch = bytecodePatch(
    name = "Gemini Chat translation router (experimental)",
    description = "Adds a Gmn toolbar icon. An explicit tap copies a translation prompt for selected, non-sensitive editor text and opens https://gemini.google.com/app. The user must paste/send it and copy the result back; no API key, automatic submission, or automatic result insertion is claimed.",
    default = false,
) {
    compatibleWith(COMPATIBILITY_GBOARD)
    dependsOn(
        gboardPatchesSettingsPatch,
        gboardGeminiRouterMarkerPatch,
        gboardGeminiRouterAssetsPatch,
        gboardAccessPointContributions1803Patch,
    )
    execute {
        check(packageMetadata.versionName == "18.5.4.993608717-release-arm64-v8a" &&
            packageMetadata.versionCode == "176049702") {
            "Gemini chat router supports only the reviewed Gboard 18.5.4 version and code"
        }
        check(mutableClass("Lphr;").superclass == "Landroid/inputmethodservice/InputMethodService;") {
            "Gboard input service changed"
        }
        val catalog = findMutableMethodOrThrow(GboardAccessPointContributionsTargets.orderFactory)
        val controller = findMutableMethodOrThrow(GboardAccessPointContributionsTargets.controllerConstructor)
        val catalogRef = RuntimeAbiCatalog.abi(RuntimeCallId.GEMINI_ROUTER_ACCESS_POINT_CATALOG).reference
        val registerRef = RuntimeAbiCatalog.abi(RuntimeCallId.GEMINI_ROUTER_ACCESS_POINT_REGISTER).reference
        check(catalog.implementation?.instructions?.none { it.isMethodReference(catalogRef) } == true) {
            "Gemini router catalog hook already exists"
        }
        check(controller.implementation?.instructions?.none { it.isMethodReference(registerRef) } == true) {
            "Gemini router registration hook already exists"
        }
        catalog.addInstructions(
            0,
            """
                move-object/from16 v0, p0
                move-object/from16 v1, p3
                ${RuntimeCallEmitter.invoke(RuntimeCallId.GEMINI_ROUTER_ACCESS_POINT_CATALOG, "v0, v1")}
                move-result-object v0
                move-object/from16 p3, v0
                check-cast p3, Lwpa;
            """.trimIndent(),
        )
        val returns = controller.returnInstructionIndices().filter {
            controller.implementation!!.instructions[it].isOpcode("RETURN_VOID")
        }
        check(returns.size == 1) { "Unexpected Gboard toolbar controller constructor" }
        controller.addInstructions(returns.single(), RuntimeCallEmitter.invoke(
            RuntimeCallId.GEMINI_ROUTER_ACCESS_POINT_REGISTER, "p0, p1",
        ))
    }
}
