#!/usr/bin/env python3
"""Validate the opt-in Instant Translate MPP and its Morphe patch listing."""
from __future__ import annotations

import argparse
import hashlib
import re
import zipfile
from pathlib import Path

from prepare_build import VERSION

NAME = 'Translation fallback (SEA-LION, experimental)'
SETTINGS_NAME = 'Settings Patch (SEA-LION, experimental)'
LICENSE_NAME = 'Remove license check (experimental)'
MICROG_NAME = 'Official microG service visibility (experimental)'
PREMIUM_NAME = 'Unlock premium local gate (experimental)'
PACKAGE = 'com.spaceship.screen.textcopy'
VERSION_NAME = 'v7.5.00300'
PATCHES = {
    NAME: ('TranslationFallbackPatchKt.class', (VERSION_NAME, 'v7.5.00307')),
    SETTINGS_NAME: ('SettingsPatchKt.class', (VERSION_NAME, 'v7.5.00307')),
    LICENSE_NAME: ('RemoveLicenseCheckPatchKt.class', ('v7.5.00307',)),
    MICROG_NAME: ('OfficialMicroGVisibilityPatchKt.class', ('v7.5.00307',)),
    PREMIUM_NAME: ('UnlockPremiumPatchKt.class', ('v7.5.00307',)),
}


def verify_bundle(bundle: Path) -> dict:
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    checksum = bundle.with_name(bundle.name + '.sha256')
    if checksum.read_text().split()[0] != digest:
        raise ValueError('MPP checksum mismatch')
    with zipfile.ZipFile(bundle) as archive:
        names = archive.namelist()
        if len(set(names)) != len(names) or archive.testzip() is not None:
            raise ValueError('Invalid MPP archive')
        manifest = archive.read('META-INF/MANIFEST.MF').decode().replace('\r\n ', '').replace('\r', '')
        for value in (f'Version: {VERSION}\n', 'Patcher-Version: 2.0.0\n', 'Instant Translate patches (experimental)'):
            if value not in manifest:
                raise ValueError('Unexpected MPP metadata: ' + value)
        for entry in ('classes.dex', 'extensions/instanttranslate.mpe'):
            if entry not in names:
                raise ValueError('Missing bundle entry: ' + entry)
        for selector, (filename, _) in PATCHES.items():
            entry = 'app/morphe/patches/instanttranslate/' + filename
            if entry not in names or selector.encode() not in archive.read(entry):
                raise ValueError('Missing patch selector: ' + selector)
        extension = archive.read('extensions/instanttranslate.mpe')
        for forbidden in (b'GtxClient', b'translate.googleapis.com', b'Google fallback'):
            if forbidden in extension:
                raise ValueError('Removed Google fallback is still present in the bundle')
        old_selector = b'Translation fallback (Google, experimental)'
        fallback = 'app/morphe/patches/instanttranslate/TranslationFallbackPatchKt.class'
        if old_selector in archive.read(fallback) or old_selector in archive.read('classes.dex'):
            raise ValueError('Removed Google fallback selector is still present')
        for value in (b'https://api.sea-lion.ai/v1/', b'aisingapore/Gemma-SEA-LION-v4-27B-IT'):
            if value not in extension:
                raise ValueError('SEA-LION configuration defaults are missing from the bundle')
        classes = [name for name in names if name.startswith('app/morphe/patches/') and name.endswith('.class')]
        if not classes or any(not name.startswith('app/morphe/patches/instanttranslate/') for name in classes):
            raise ValueError('Unrelated app patches present in standalone bundle')
    return {'sha256': digest, 'bytes': bundle.stat().st_size, 'version': VERSION,
            'selectors': {name: version for name, (_, version) in PATCHES.items()}}


def verify_listing(text: str) -> None:
    cards = re.findall(r'^Name: (.+?)\s*\n(.*?)(?=^Name: |\Z)', text, flags=re.MULTILINE | re.DOTALL)
    if len(cards) != len(PATCHES) or set(name for name, _ in cards) != set(PATCHES):
        raise ValueError('Unexpected patch selectors')
    for name, body in cards:
        enabled = re.findall(r'^Enabled: (true|false)$', body, flags=re.MULTILINE | re.IGNORECASE)
        packages = re.findall(r'^\s*Package name: (\S+)', body, flags=re.MULTILINE)
        versions = re.findall(r'^[ \t]*(v\d+\.\d+\.\d+)[ \t]*$', body, flags=re.MULTILINE)
        if [value.lower() for value in enabled] != ['false']:
            raise ValueError('Patch is not opt-in: ' + name)
        if packages != [PACKAGE] or sorted(versions) != sorted(PATCHES[name][1]):
            raise ValueError('Unexpected target for patch: ' + name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mpp', required=True, type=Path)
    parser.add_argument('--listing', type=Path)
    args = parser.parse_args()
    print('Verified Instant Translate-only bundle:', verify_bundle(args.mpp))
    if args.listing:
        verify_listing(args.listing.read_text())
        print('Morphe lists the exact opt-in selectors and target versions')


if __name__ == '__main__':
    main()
