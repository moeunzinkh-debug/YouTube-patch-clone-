#!/usr/bin/env python3
"""Validate the King-only MPP and Morphe Desktop patch listing."""
from __future__ import annotations
import argparse
import hashlib
import re
import zipfile
from pathlib import Path
from prepare_build import VERSION

PATCHES = ('Remove license (new Google Play LVL method)', 'Remove insignificant things (manual UI selection)')
PACKAGE = 'ru.jgaiecip.osuojvyxe'

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
        for expected in (f'Version: {VERSION}\n', 'Patcher-Version: 2.0.0\n', 'King-Patcher experimental patches'):
            if expected not in manifest:
                raise ValueError('Unexpected bundle metadata: ' + expected)
        klass = archive.read('app/morphe/patches/king/KingPatchesKt.class')
        for name in PATCHES:
            if name.encode() not in klass:
                raise ValueError('Patch selector missing: ' + name)
        extension = archive.read('extensions/king.mpe')
        if 'classes.dex' not in names or not extension.startswith(b'dex\n'):
            raise ValueError('Patch or extension DEX missing')
        for needed in (b'Lapp/morphe/extension/king/ToolActivity;', b'Lapp/morphe/extension/king/LvlEditor;',
                       b'Lapp/morphe/extension/king/AxmlEditor;', b'Lapp/morphe/extension/king/ApkSignerBridge;'):
            if needed not in extension:
                raise ValueError('Extension class missing')
        # The host supplies these libraries. Packaging copies into an extension would collide.
        if b'Lorg/jf/dexlib2/DexFileFactory;' not in extension:
            raise ValueError('Expected host dexlib2 reference missing')
        classes = [name for name in names if name.startswith('app/morphe/patches/') and name.endswith('.class')]
        if not classes or any(not name.startswith('app/morphe/patches/king/') for name in classes):
            raise ValueError('Unrelated patches in King-only bundle')
    cards = re.findall(r'^Name: (.+?)\s*\n(.*?)(?=^Name: |\Z)', listing, flags=re.MULTILINE | re.DOTALL)
    if len(cards) != len(PATCHES) or set(name for name, _ in cards) != set(PATCHES):
        raise ValueError('Unexpected patch listing')
    for name, body in cards:
        enabled = re.findall(r'^Enabled: (true|false)$', body, flags=re.MULTILINE | re.IGNORECASE)
        packages = re.findall(r'^\s*Package name: (\S+)', body, flags=re.MULTILINE)
        versions = re.findall(r'^[ \t]*(\d+\.\d+\.\d+)[ \t]*$', body, flags=re.MULTILINE)
        if [v.lower() for v in enabled] != ['false'] or packages != [PACKAGE] or versions != ['12.10.10']:
            raise ValueError('Unexpected opt-in setting or target: ' + name)
    return {'sha256': digest, 'bytes': bundle.stat().st_size, 'version': VERSION, 'patches': list(PATCHES)}

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mpp', required=True, type=Path)
    parser.add_argument('--listing', required=True, type=Path)
    args = parser.parse_args()
    print(verify(args.mpp, args.listing.read_text()))

if __name__ == '__main__':
    main()
