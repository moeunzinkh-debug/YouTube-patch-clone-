#!/usr/bin/env python3
"""Validate the isolated GenV MPP and its Morphe Desktop selector listing."""
from __future__ import annotations
import argparse
import hashlib
import re
import zipfile
from pathlib import Path
from prepare_build import VERSION

NAME = 'Remove license check'
MICROG = 'Morphe MicroG Google sign-in support (experimental)'
PACKAGE = 'com.ainate.ai.video.generate'
PATCH_DEFAULTS = {NAME: True, MICROG: False}


def verify_listing(text: str) -> None:
    cards = re.findall(r'^Name: (.+?)\s*\n(.*?)(?=^Name: |\Z)', text, flags=re.MULTILINE | re.DOTALL)
    if len(cards) != len(PATCH_DEFAULTS) or {name for name, _ in cards} != set(PATCH_DEFAULTS):
        raise ValueError('Unexpected patch listing')
    for name, body in cards:
        enabled = re.findall(r'^Enabled: (true|false)$', body, flags=re.MULTILINE | re.IGNORECASE)
        packages = re.findall(r'^\s*Package name: (\S+)', body, flags=re.MULTILINE)
        versions = re.findall(r'^[ \t]*(\d+\.\d+\.\d+)[ \t]*$', body, flags=re.MULTILINE)
        if [v.lower() for v in enabled] != [str(PATCH_DEFAULTS[name]).lower()] or packages != [PACKAGE] or versions != ['3.7.2']:
            raise ValueError('Unexpected selector default or compatibility: ' + name)


def verify(bundle: Path, listing: str) -> dict:
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    checksum = bundle.with_name(bundle.name + '.sha256')
    if checksum.read_text().split()[0] != digest:
        raise ValueError('Bundle checksum mismatch')
    with zipfile.ZipFile(bundle) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or archive.testzip() is not None:
            raise ValueError('Invalid bundle ZIP')
        manifest = archive.read('META-INF/MANIFEST.MF').decode().replace('\r\n ', '').replace('\r', '')
        for expected in (f'Version: {VERSION}\n', 'Patcher-Version: 2.0.0\n', 'GenV patches (experimental)'):
            if expected not in manifest:
                raise ValueError('Unexpected bundle metadata: ' + expected)
        klass = archive.read('app/morphe/patches/genv/RemoveLicenseCheckPatchKt.class')
        if NAME.encode() not in klass:
            raise ValueError('License selector missing')
        klass = archive.read('app/morphe/patches/genv/MorpheMicroGSupportPatchKt.class')
        if MICROG.encode() not in klass:
            raise ValueError('Morphe MicroG selector missing')
        extension = archive.read('extensions/genv.mpe')
        if 'classes.dex' not in names or not extension.startswith(b'dex\n') or b'Lapp/morphe/extension/genv/MicroGGuard;' not in extension:
            raise ValueError('Patch or MicroG guard extension DEX missing')
        classes = [name for name in names if name.startswith('app/morphe/patches/') and name.endswith('.class')]
        if not classes or any(not name.startswith('app/morphe/patches/genv/') for name in classes):
            raise ValueError('Unrelated patch classes in GenV-only bundle')
    verify_listing(listing)
    return {'sha256': digest, 'bytes': bundle.stat().st_size, 'version': VERSION,
            'patches': list(PATCH_DEFAULTS), 'experimental': True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mpp', required=True, type=Path)
    parser.add_argument('--listing', required=True, type=Path)
    args = parser.parse_args()
    print(verify(args.mpp, args.listing.read_text()))


if __name__ == '__main__':
    main()
