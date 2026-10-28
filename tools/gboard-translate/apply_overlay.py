#!/usr/bin/env python3
"""Create an isolated experimental fork from the untouched, verified upstream tree."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = ROOT / "extras/gboard-patches"
OVERLAY = ROOT / "tools/gboard-translate/overlay"
VERSION = "4.0.0-direct-translate-dev.1"
PATCH_NAME = "Direct Google Translate (experimental)"


def replace_once(path: Path, old: str, new: str) -> None:
    value = path.read_text(encoding="utf-8")
    if value.count(old) != 1:
        raise SystemExit(f"Fork overlay expected exactly one anchor in {path.name}: {old!r}")
    path.write_text(value.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="new temporary build directory")
    args = parser.parse_args()
    destination = args.destination.resolve()
    if destination.exists() or destination == ROOT or ROOT in destination.parents:
        raise SystemExit("Destination must be a new directory outside the repository")
    subprocess.run([sys.executable, str(ROOT / "tools/gboard/verify_vendor.py")], check=True)
    shutil.copytree(UPSTREAM, destination, ignore=shutil.ignore_patterns(".git", ".gradle", "build"))
    for source in sorted(OVERLAY.rglob("*")):
        if source.is_file():
            target = destination / source.relative_to(OVERLAY)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    replace_once(destination / "gradle.properties", "version = 4.0.0\n", f"version = {VERSION}\n")
    patch_gradle = destination / "patches/build.gradle.kts"
    replace_once(patch_gradle, '        name = "Gboard Patches"',
                 '        name = "Gboard Patches - Direct Translate experimental fork"')
    replace_once(patch_gradle, '        description = "Morphe patches for Gboard."',
                 '        description = "Experimental Translate fork of jasonwu1994/Gboard-patches v4.0.0."')
    replace_once(patch_gradle, '        author = "Jason Wu"',
                 '        author = "Jason Wu (upstream); Translate overlay by fork maintainers"')
    replace_once(patch_gradle, '        source = "https://github.com/jasonwu1994/gboard-patches"',
                 '        source = "https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/arena/69154a0c-youtube-patch-clone/tools/gboard-translate"')
    replace_once(patch_gradle, '        contact = "https://github.com/jasonwu1994/gboard-patches/issues"',
                 '        contact = "https://github.com/moeunzinkh-debug/YouTube-patch-clone-/issues"')
    replace_once(patch_gradle, '        website = "https://github.com/jasonwu1994/gboard-patches"',
                 '        website = "https://github.com/moeunzinkh-debug/YouTube-patch-clone-"')
    registry = destination / "patches/src/main/kotlin/dev/jason/gboardpatches/patches/gboard/registry/GboardPatchRegistry.kt"
    replace_once(registry, "import app.morphe.patcher.patch.Patch\n",
                 "import app.morphe.patcher.patch.Patch\n"
                 "import dev.jason.gboardpatches.patches.gboard.features.directtranslate.gboardDirectGoogleTranslatePatch\n")
    replace_once(registry, "        gboardSignatureBypassPatch,\n    ).filterTo",
                 "        gboardSignatureBypassPatch,\n        gboardDirectGoogleTranslatePatch,\n    ).filterTo")
    verifier = destination / "patches/src/main/kotlin/dev/jason/gboardpatches/patches/gboard/registry/GboardCapabilityWiringVerifier.kt"
    replace_once(verifier, "        }.toSet()\n        val actualPatchNames",
                 f'        }}.toSet() + "{PATCH_NAME}"\n        val actualPatchNames')
    abi = destination / "patches/src/main/kotlin/dev/jason/gboardpatches/patches/gboard/shared/runtimeabi/RuntimeAbi.kt"
    replace_once(abi, "internal enum class RuntimeCallId(internal val encodedAbi: String) {\n",
                 "internal enum class RuntimeCallId(internal val encodedAbi: String) {\n"
                 '    DIRECT_TRANSLATE_TRY_DISPATCH("Ldev/jason/gboardpatches/extension/directtranslate/GboardDirectTranslateRuntime;->tryDispatch(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Z"),\n'
                 '    DIRECT_TRANSLATE_PREPARE("Ldev/jason/gboardpatches/extension/directtranslate/GboardDirectTranslateRuntime;->prepare(Ljava/lang/Object;Ljava/lang/Object;)V"),\n'
                 '    DIRECT_TRANSLATE_CANCEL("Ldev/jason/gboardpatches/extension/directtranslate/GboardDirectTranslateRuntime;->cancel()V"),\n')
    extension_gradle = destination / "extensions/extension/build.gradle.kts"
    replace_once(extension_gradle, '    testImplementation("junit:junit:4.13.2")\n',
                 '    testImplementation("junit:junit:4.13.2")\n'
                 '    testImplementation("org.json:json:20240303")\n')
    replace_once(extension_gradle, r'"https://github.com/jasonwu1994/Gboard-patches\"',
                 r'"https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/arena/69154a0c-youtube-patch-clone/tools/gboard-translate\"')
    (destination / "gradlew").chmod(0o755)
    print(f"Created experimental {VERSION} fork at {destination}; pinned upstream tree was not modified.")


if __name__ == "__main__":
    main()
