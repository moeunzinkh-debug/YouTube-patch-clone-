#!/usr/bin/env python3
"""Verify a Kimi-only MPP and, when supplied, Morphe's actual listing."""
from __future__ import annotations

import argparse
import hashlib
import re
import zipfile
from pathlib import Path

from prepare_build import VERSION

NAME = 'Remove license check'
PACKAGE = 'com.moonshot.kimichat'


def verify_bundle(bundle: Path) -> dict:
    checksum = bundle.with_name(bundle.name + '.sha256')
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    if checksum.read_text().split()[0] != digest:
        raise ValueError('Kimi bundle checksum mismatch')
    with zipfile.ZipFile(bundle) as archive:
        names = archive.namelist()
        if len(set(names)) != len(names) or archive.testzip() is not None:
            raise ValueError('Invalid MPP archive')
        manifest = archive.read('META-INF/MANIFEST.MF').decode().replace('\r\n ', '').replace('\r', '')
        for text in (f'Version: {VERSION}\n', 'Patcher-Version: 2.0.0\n', 'Kimi patches (experimental)'):
            if text not in manifest:
                raise ValueError('Unexpected MPP metadata: ' + text)
        required = 'app/morphe/patches/kimi/RemoveLicenseCheckPatchKt.class'
        if 'classes.dex' not in names or required not in names or NAME.encode() not in archive.read(required):
            raise ValueError('Missing Kimi patch class or Android DEX')
        project_classes = [name for name in names if name.startswith('app/morphe/patches/') and name.endswith('.class')]
        if not project_classes or any(not name.startswith('app/morphe/patches/kimi/') for name in project_classes):
            raise ValueError('Unrelated app patch classes present in Kimi bundle')
    return {'sha256': digest, 'bytes': bundle.stat().st_size, 'version': VERSION}


def verify_listing(text: str) -> None:
    names = re.findall(r'^Name: (.+)$', text, flags=re.MULTILINE)
    enabled = re.findall(r'^Enabled: (true|false)$', text, flags=re.MULTILINE | re.IGNORECASE)
    packages = re.findall(r'^\s*Package name: (\S+)', text, flags=re.MULTILINE)
    if names != [NAME] or [value.lower() for value in enabled] != ['true']:
        raise ValueError('Unexpected Kimi selector or default')
    if packages != [PACKAGE] or not re.search(r'^\s*3\.1\.5\s*$', text, flags=re.MULTILINE):
        raise ValueError('Unexpected Kimi package or version target')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mpp', required=True, type=Path)
    parser.add_argument('--listing', type=Path)
    args = parser.parse_args()
    print('Verified Kimi-only bundle:', verify_bundle(args.mpp))
    if args.listing:
        verify_listing(args.listing.read_text())
        print('Morphe lists exactly the requested Kimi selector for 3.1.5')


if __name__ == '__main__':
    main()
