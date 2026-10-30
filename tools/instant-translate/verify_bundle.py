#!/usr/bin/env python3
"""Validate the exact opt-in Instant Translate MPP and Morphe listing."""
from __future__ import annotations

import argparse
import hashlib
import re
import zipfile
from pathlib import Path

from prepare_build import VERSION

NAME = 'Translation fallback (Google, experimental)'
PACKAGE = 'com.spaceship.screen.textcopy'
VERSION_NAME = 'v7.5.00300'


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
        required = 'app/morphe/patches/instanttranslate/TranslationFallbackPatchKt.class'
        for entry in ('classes.dex', 'extensions/instanttranslate.mpe', required):
            if entry not in names:
                raise ValueError('Missing bundle entry: ' + entry)
        if NAME.encode() not in archive.read(required):
            raise ValueError('Missing opt-in translation selector')
        classes = [name for name in names if name.startswith('app/morphe/patches/') and name.endswith('.class')]
        if not classes or any(not name.startswith('app/morphe/patches/instanttranslate/') for name in classes):
            raise ValueError('Unrelated app patches present in standalone bundle')
    return {'sha256': digest, 'bytes': bundle.stat().st_size, 'version': VERSION}


def verify_listing(text: str) -> None:
    names = re.findall(r'^Name: (.+)$', text, flags=re.MULTILINE)
    enabled = re.findall(r'^Enabled: (true|false)$', text, flags=re.MULTILINE | re.IGNORECASE)
    packages = re.findall(r'^\s*Package name: (\S+)', text, flags=re.MULTILINE)
    if names != [NAME] or [value.lower() for value in enabled] != ['false']:
        raise ValueError('Unexpected patch selector or opt-in default')
    if packages != [PACKAGE] or not re.search(r'^\s*v7\.5\.00300\s*$', text, flags=re.MULTILINE):
        raise ValueError('Unexpected app package or version target')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mpp', required=True, type=Path)
    parser.add_argument('--listing', type=Path)
    args = parser.parse_args()
    print('Verified Instant Translate-only bundle:', verify_bundle(args.mpp))
    if args.listing:
        verify_listing(args.listing.read_text())
        print('Morphe lists exactly the opt-in selector for the reviewed version')


if __name__ == '__main__':
    main()
