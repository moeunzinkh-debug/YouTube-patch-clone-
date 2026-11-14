#!/usr/bin/env python3
"""Create a disposable, unsigned hybrid for the emulator; NEVER distribute it.

The input is a third-party prepatched Gboard, not stock. Keep the actual
patched manifest so the real Khmerlish activity and feature marker are tested.
Restore the renamed test package and its Patches provider authority within the
binary XML string pool, plus the resource-table name and settings intents, so
this disposable hybrid can coexist with system Gboard. DEX, assets, and
resources come from the actual Morphe output. Alignment and signing happen later.
"""
from pathlib import Path
import argparse
import re
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/gboard-translate'))
import make_manifest_fixture as binary_xml  # noqa: E402
from make_fixture import replace_resource_package  # noqa: E402
from axml_fixture import rewrite_pool_string  # noqa: E402

CALCULATOR = 'dev.jason.gboardpatches.feature.simple_calculator'
KHMERLISH = 'dev.jason.gboardpatches.feature.khmerlish'
GEMINI = 'dev.jason.gboardpatches.feature.gemini_router'
DICTIONARY_ACTIVITY = 'dev.jason.gboardpatches.extension.khmerlish.KhmerlishDictionaryActivity'
PROVIDER_SUFFIX = '.gboard_patches'
DEX = re.compile(r'classes(?:[2-9]|[1-9][0-9]+)?\.dex\Z')
SIGNATURE = re.compile(r'META-INF/[^/]+\.(?:SF|RSA|DSA|EC)\Z', re.IGNORECASE)
ASSETS = ('assets/gboard-khmer/dictionary.tsv', 'assets/gboard-khmer/LICENSE.txt')


def rewrite_test_manifest(manifest: bytes) -> bytes:
    """Restore only test package strings while retaining actual patched components."""
    contains = lambda value: any(value.encode(enc) in manifest for enc in ('utf-8', 'utf-16le'))
    if not all(contains(value) for value in (KHMERLISH, GEMINI, DICTIONARY_ACTIVITY, CALCULATOR)):
        raise ValueError('Patched manifest is missing a required activity or feature marker')
    manifest = rewrite_pool_string(manifest, binary_xml.NEW, binary_xml.OLD)
    return rewrite_pool_string(manifest, binary_xml.NEW + PROVIDER_SUFFIX, binary_xml.OLD + PROVIDER_SUFFIX)


def build(original: Path, patched: Path, output: Path) -> int:
    if output.exists() or output.resolve() in (original.resolve(), patched.resolve()):
        raise ValueError('Output must be a new file')
    with zipfile.ZipFile(original) as source, zipfile.ZipFile(patched) as result:
        dexes = [entry for entry in result.infolist() if DEX.fullmatch(entry.filename)]
        names = result.namelist()
        if not dexes or len({x.filename for x in dexes}) != len(dexes) or 'classes.dex' not in names:
            raise ValueError('Missing or duplicate patched DEX files')
        if (source.namelist().count('AndroidManifest.xml') != 1
                or names.count('AndroidManifest.xml') != 1 or names.count('resources.arsc') != 1
                or any(names.count(x) != 1 for x in ASSETS)):
            raise ValueError('Missing manifest, resource table or Khmerlish assets')
        new_resources = [x for x in result.infolist()
                         if x.filename.startswith(('res/', 'assets/'))]
        with zipfile.ZipFile(output, 'w') as destination:
            for entry in source.infolist():
                if (DEX.fullmatch(entry.filename) or SIGNATURE.fullmatch(entry.filename)
                        or entry.filename == 'resources.arsc'
                        or entry.filename.startswith(('res/', 'assets/'))):
                    continue
                if entry.filename == 'AndroidManifest.xml':
                    destination.writestr(entry, rewrite_test_manifest(result.read('AndroidManifest.xml')))
                else:
                    with source.open(entry) as src, destination.open(entry, 'w') as dst:
                        shutil.copyfileobj(src, dst, 1024 * 1024)
            table = replace_resource_package(result.read('resources.arsc'), binary_xml.NEW, binary_xml.OLD)
            destination.writestr(result.getinfo('resources.arsc'), table)
            settings_count = 0
            for entry in dexes + new_resources:
                if entry.filename.startswith('res/') and entry.filename.endswith('.xml'):
                    data = result.read(entry)
                    marker = 'gboard_patches_entry'
                    activity = 'dev.jason.gboardpatches.extension.settings.GboardPatchesSettingsActivity'
                    contains = lambda text: text.encode('utf-8') in data or text.encode('utf-16le') in data
                    if contains(marker) and contains(activity):
                        data = rewrite_pool_string(data, binary_xml.NEW, binary_xml.OLD)
                        settings_count += 1
                    destination.writestr(entry, data)
                else:
                    with result.open(entry) as src, destination.open(entry, 'w') as dst:
                        shutil.copyfileobj(src, dst, 1024 * 1024)
            if settings_count < 2:
                raise ValueError(f'Expected both Patches settings XMLs; found {settings_count}')
    return len(dexes)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('patched', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    count = build(args.original, args.patched, args.output)
    print(f'Created a temporary, unsigned, non-stock emulator hybrid with {count} patched DEX files.')


if __name__ == '__main__':
    main()
