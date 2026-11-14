#!/usr/bin/env python3
"""Check the built MPP preserves existing registrations and includes the offline feature."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
VERSION = '4.0.8-khmerlish-dev.1'
NAME = 'Khmerlish to Khmer (experimental)'
GEMINI_NAME = 'Gemini Chat translation router (experimental)'
PACKAGE = 'com.google.android.inputmethod.latin'
TARGET = '18.5.4.993608717-release-arm64-v8a'


def verify(bundle: Path, metadata: Path, listing: Path) -> str:
    previous = json.loads((ROOT / 'bundles/gboard-experimental/patches-list.json').read_text())
    actual = json.loads(metadata.read_text())
    if actual.get('version') != VERSION:
        raise ValueError('Incorrect fork version')
    patches = actual['patches']
    extra = [patch for patch in patches if patch['name'] == NAME]
    gemini = [patch for patch in patches if patch['name'] == GEMINI_NAME]
    if (len(patches) != 46 or len(extra) != 1 or len(gemini) != 1
            or extra[0]['use'] is not False or gemini[0]['use'] is not False):
        raise ValueError('Expected 43 upstream + Direct Translate + opt-in Gemini and Khmerlish')
    if (extra[0]['compatiblePackages'] != {PACKAGE: [TARGET]}
            or gemini[0]['compatiblePackages'] != {PACKAGE: [TARGET]}):
        raise ValueError('Unexpected experimental patch compatibility')
    if [patch for patch in patches if patch['name'] not in {NAME, GEMINI_NAME}] != previous['patches']:
        raise ValueError('Existing Gboard or Direct Translate registrations changed')
    text = listing.read_text()
    names = re.findall(r'^Name: (.+)$', text, flags=re.MULTILINE)
    enabled = re.findall(r'^Enabled: (.+)$', text, flags=re.MULTILINE)
    if len(names) != 46 or set(names) != {patch['name'] for patch in patches} or len(enabled) != 46:
        raise ValueError('Morphe Desktop did not load all 46 registrations')
    if sum(value.lower() == 'true' for value in enabled) != 43:
        raise ValueError('Existing defaults or experimental opt-in defaults changed')
    if text.count('Package name: ' + PACKAGE) != 46 or text.count(TARGET) != 46:
        raise ValueError('Unexpected target metadata')
    resource = ROOT / 'tools/gboard-khmer/overlay/patches/src/main/resources/gboard-khmer'
    with zipfile.ZipFile(bundle) as archive:
        if archive.testzip() is not None:
            raise ValueError('Corrupted MPP')
        required = {'META-INF/MANIFEST.MF', 'classes.dex', 'extensions/gboard-patches.rve',
                    'gboard-khmer/dictionary.tsv', 'gboard-khmer/predictions.tsv',
                    'gboard-khmer/LICENSE.txt', 'gboard-khmer/gboard_khmerlish_panel.xml',
                    'gboard-gemini/gboard_gemini_chat.xml'}
        if not required.issubset(archive.namelist()):
            raise ValueError(f'Missing MPP files: {required - set(archive.namelist())}')
        for filename in ('dictionary.tsv', 'predictions.tsv', 'LICENSE.txt', 'gboard_khmerlish_panel.xml'):
            if archive.read(f'gboard-khmer/{filename}') != (resource / filename).read_bytes():
                raise ValueError(f'MPP resource differs from checked-in source: {filename}')
        gemini_icon = ROOT / 'tools/gboard-khmer/overlay/patches/src/main/resources/gboard-gemini/gboard_gemini_chat.xml'
        if archive.read('gboard-gemini/gboard_gemini_chat.xml') != gemini_icon.read_bytes():
            raise ValueError('MPP Gemini toolbar icon differs from checked-in source')
        dex = archive.read('extensions/gboard-patches.rve')
        if not dex.startswith(b'dex\n'):
            raise ValueError('Extension is not Android DEX')
        for marker in (b'KhmerlishRuntime', b'KhmerlishController', b'KhmerlishSettingsFeature',
                       b'KhmerlishPanelRuntime', b'KhmerlishPanelSession', b'KhmerlishPanelConverter',
                       b'KhmerlishPanelCommitter', b'KhmerlishAccessPoint', b'KhmerlishDictionaryActivity',
                       b'KhmerlishPersonalData', b'KhmerlishPersonalStore', b'KhmerlishWordGuide',
                       b'GeminiAccessPoint', b'GeminiChatRouter', b'https://gemini.google.com/app',
                       b'GboardDirectTranslateRuntime'):
            if marker not in dex:
                raise ValueError(f'Missing extension class: {marker!r}')
        manifest = archive.read('META-INF/MANIFEST.MF').decode('utf-8').replace('\r\n ', '')
        if VERSION not in manifest or 'experimental fork' not in manifest:
            raise ValueError('Manifest does not identify the experimental fork')
        if 'Jason Wu' not in manifest or 'moeunzinkh-debug/YouTube-patch-clone-' not in manifest:
            raise ValueError('Upstream/fork attribution missing')
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    print(f'Verified MPP: {bundle.stat().st_size} bytes, SHA-256 {digest}')
    print('Morphe Desktop loaded 43 unchanged upstream entries and three opt-in fork entries.')
    return digest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('metadata', type=Path)
    parser.add_argument('listing', type=Path)
    args = parser.parse_args()
    verify(args.bundle, args.metadata, args.listing)


if __name__ == '__main__':
    main()
