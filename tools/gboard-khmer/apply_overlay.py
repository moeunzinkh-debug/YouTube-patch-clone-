#!/usr/bin/env python3
"""Build an isolated Gboard fork with the existing Translate overlay and Khmerlish."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OVERLAY = ROOT / 'tools/gboard-khmer/overlay'
VERSION = '4.0.6-khmerlish-dev.1'
PATCH_NAME = 'Khmerlish to Khmer (experimental)'
SOURCE = 'https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/arena/86d53cf2-youtube-patch-clone/tools/gboard-khmer'


def replace_once(path: Path, old: str, new: str) -> None:
    data = path.read_text(encoding='utf-8')
    if data.count(old) != 1:
        raise SystemExit(f'Expected exactly one anchor in {path}: {old!r}')
    path.write_text(data.replace(old, new, 1), encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    destination = args.destination.resolve()
    if destination.exists() or destination == ROOT or ROOT in destination.parents:
        raise SystemExit('Destination must be a new directory outside the repository')
    subprocess.run([sys.executable, str(ROOT / 'tools/gboard-khmer/build_dictionary.py'), '--check'], check=True)
    # This verifies the pinned upstream tree and retains the previously built
    # Direct Google Translate experimental patch as well as all 43 upstream patches.
    subprocess.run([sys.executable, str(ROOT / 'tools/gboard-translate/apply_overlay.py'),
                    str(destination)], check=True)
    for source in sorted(OVERLAY.rglob('*')):
        if source.is_file():
            target = destination / source.relative_to(OVERLAY)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    replace_once(destination / 'gradle.properties', 'version = 4.0.0-direct-translate-dev.2\n',
                 f'version = {VERSION}\n')
    gradle = destination / 'patches/build.gradle.kts'
    replace_once(gradle, 'name = "Gboard Patches - Direct Translate experimental fork"',
                 'name = "Gboard Patches - Khmerlish experimental fork"')
    replace_once(gradle, 'description = "Experimental Translate fork of jasonwu1994/Gboard-patches v4.0.0."',
                 'description = "Experimental Khmerlish and Translate fork of jasonwu1994/Gboard-patches v4.0.0."')
    replace_once(gradle, 'author = "Jason Wu (upstream); Translate overlay by fork maintainers"',
                 'author = "Jason Wu (upstream); Khmerlish and Translate overlays by fork maintainers"')
    replace_once(gradle, 'https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/arena/69154a0c-youtube-patch-clone/tools/gboard-translate', SOURCE)
    ext_gradle = destination / 'extensions/extension/build.gradle.kts'
    replace_once(ext_gradle, 'https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/arena/69154a0c-youtube-patch-clone/tools/gboard-translate', SOURCE)

    registry = destination / 'patches/src/main/kotlin/dev/jason/gboardpatches/patches/gboard/registry/GboardPatchRegistry.kt'
    replace_once(registry,
                 'import dev.jason.gboardpatches.patches.gboard.features.directtranslate.gboardDirectGoogleTranslatePatch\n',
                 'import dev.jason.gboardpatches.patches.gboard.features.directtranslate.gboardDirectGoogleTranslatePatch\n'
                 'import dev.jason.gboardpatches.patches.gboard.features.khmerlish.gboardKhmerlishPatch\n')
    replace_once(registry, '        gboardDirectGoogleTranslatePatch,\n    ).filterTo',
                 '        gboardDirectGoogleTranslatePatch,\n        gboardKhmerlishPatch,\n    ).filterTo')
    verifier = destination / 'patches/src/main/kotlin/dev/jason/gboardpatches/patches/gboard/registry/GboardCapabilityWiringVerifier.kt'
    replace_once(verifier, '}.toSet() + "Direct Google Translate (experimental)"',
                 f'}}.toSet() + "Direct Google Translate (experimental)" + "{PATCH_NAME}"')
    abi = destination / 'patches/src/main/kotlin/dev/jason/gboardpatches/patches/gboard/shared/runtimeabi/RuntimeAbi.kt'
    replace_once(abi, 'internal enum class RuntimeCallId(internal val encodedAbi: String) {\n',
                 'internal enum class RuntimeCallId(internal val encodedAbi: String) {\n'
                 '    KHMERLISH_ON_SELECTION("Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishRuntime;->onSelection(Landroid/inputmethodservice/InputMethodService;IIIIII)V"),\n'
                 '    KHMERLISH_ON_INPUT_VIEW_STARTED("Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishRuntime;->onInputViewStarted(Landroid/inputmethodservice/InputMethodService;)V"),\n'
                 '    KHMERLISH_RESET("Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishRuntime;->reset(Landroid/inputmethodservice/InputMethodService;)V"),\n'
                 '    KHMERLISH_ACCESS_POINT_CATALOG("Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishAccessPoint;->extendOrderCatalog(Landroid/content/Context;Ljava/lang/Object;)Ljava/lang/Object;"),\n'
                 '    KHMERLISH_ACCESS_POINT_REGISTER("Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishAccessPoint;->register(Ljava/lang/Object;Landroid/content/Context;)V"),\n'
                 '    KHMERLISH_ADD_SETTINGS("Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishSettingsFeature;->append(Landroid/content/Context;Ljava/util/List;)V"),\n')
    print(f'Created {VERSION} with upstream, Direct Translate and Khmerlish at {destination}.')


if __name__ == '__main__':
    main()
