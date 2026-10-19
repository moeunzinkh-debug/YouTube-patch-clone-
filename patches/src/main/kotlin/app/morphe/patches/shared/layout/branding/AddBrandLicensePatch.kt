package app.morphe.patches.shared.layout.branding

import app.morphe.patcher.patch.PatchException
import app.morphe.patcher.patch.rawResourcePatch
import app.morphe.util.inputStreamFromBundledResource
import java.nio.file.Files

/**
 * Copies the license and branding notice files to the target apk.
 */
internal val addLicensePatch = rawResourcePatch {
    execute {
        arrayOf(
            "MORPHE_BRANDING.TXT",
            "MORPHE_LICENSE.TXT",
            "MORPHE_LICENSE_NOTICE.TXT"
        ).forEach { sourceFileName ->
            val targetFile = get(sourceFileName, false).toPath()

            // Check if target file exists and give a more informative error
            // because Files.copy throws an exception if the file already exists.
            if (Files.exists(targetFile)) {
                throw PatchException(
                    "\n\n\n" +
                            "!!!\n" +
                            "!!!\n" +
                            "!!! Morphe branding/license file already exists in the target APK\n" +
                            "!!! (File: $sourceFileName)\n" +
                            "!!! The input APK may already be patched, or overlapping patch sources\n" +
                            "!!! may have written this file during the current patching session.\n" +
                            "!!! Start a new session with an original, unmodified APK.\n" +
                            "!!! Select patches from ONE source only: either Morphe Patches\n" +
                            "!!! or YouTube Patch Clone, not both. The clone includes shared patches.\n" +
                            "!!! Do not delete this marker or overwrite it to force re-patching.\n" +
                            "!!!\n" +
                            "!!!\n\n"
                )
            }

            inputStreamFromBundledResource("license", sourceFileName)!!.use { inputFileStream ->
                Files.copy(inputFileStream, targetFile)
            }
        }
    }
}
