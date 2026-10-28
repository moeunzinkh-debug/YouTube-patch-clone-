package app.morphe.patches.youtube.video.audio

import app.morphe.patcher.extensions.InstructionExtensions.addInstruction
import app.morphe.patcher.extensions.InstructionExtensions.getInstruction
import app.morphe.patcher.patch.bytecodePatch
import app.morphe.patcher.patch.resourcePatch
import app.morphe.patches.shared.misc.settings.preference.NonInteractivePreference
import app.morphe.patches.shared.misc.settings.preference.SwitchPreference
import app.morphe.patches.youtube.misc.playercontrols.addTopControl
import app.morphe.patches.youtube.misc.playercontrols.initializeTopControl
import app.morphe.patches.youtube.misc.playercontrols.legacyPlayerControlsPatch
import app.morphe.patches.youtube.misc.playercontrols.legacyPlayerControlsResourcePatch
import app.morphe.patches.youtube.layout.player.icons.copyPlayerButtonIcons
import app.morphe.patches.youtube.misc.extension.sharedExtensionPatch
import app.morphe.patches.youtube.misc.settings.PreferenceScreen
import app.morphe.patches.youtube.misc.settings.settingsPatch
import app.morphe.patches.youtube.shared.Constants.COMPATIBILITY_YOUTUBE
import com.android.tools.smali.dexlib2.iface.instruction.OneRegisterInstruction

private val equalizerResourcesPatch = resourcePatch {
    dependsOn(legacyPlayerControlsResourcePatch)
    execute {
        copyPlayerButtonIcons("equalizer", "morphe_equalizer_button")
        document("AndroidManifest.xml").use { document ->
            val root = document.documentElement
            val permission = "android.permission.MODIFY_AUDIO_SETTINGS"
            val permissions = document.getElementsByTagName("uses-permission")
            val exists = (0 until permissions.length).any {
                (permissions.item(it) as org.w3c.dom.Element).getAttribute("android:name") == permission
            }
            if (!exists) {
                val node = document.createElement("uses-permission")
                node.setAttribute("android:name", permission)
                root.appendChild(node)
            }
        }
    }
    finalize {
        addTopControl("equalizer", "@+id/morphe_equalizer_button", "@+id/morphe_equalizer_button")
    }
}

@Suppress("unused")
val equalizerPatch = bytecodePatch(
    name = "Audio equalizer",
    description = "Adds an in-app audio equalizer with device-supported bands, presets, reset and a top-player shortcut."
) {
    dependsOn(sharedExtensionPatch, settingsPatch, legacyPlayerControlsPatch, equalizerResourcesPatch)
    compatibleWith(COMPATIBILITY_YOUTUBE)
    execute {
        initializeTopControl("Lapp/morphe/extension/youtube/videoplayer/EqualizerPlayerButton;")
        PreferenceScreen.VIDEO.addPreferences(
            SwitchPreference("morphe_equalizer_player_button", summary = true),
            NonInteractivePreference(
                key = "morphe_equalizer",
                selectable = true,
                tag = "app.morphe.extension.youtube.settings.preference.EqualizerPreference"
            )
        )
        AudioTrackSessionIdFingerprint.let {
            it.method.apply {
                val index = it.instructionMatches.last().index
                val register = getInstruction<OneRegisterInstruction>(index).registerA
                addInstruction(index + 1,
                    "invoke-static { v$register }, Lapp/morphe/extension/youtube/patches/EqualizerPatch;->onAudioSessionId(I)V")
            }
        }
    }
}
