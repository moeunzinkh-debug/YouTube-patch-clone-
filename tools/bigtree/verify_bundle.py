#!/usr/bin/env python3
"""Verify the standalone BigTree MPP and Morphe selector listing."""
from __future__ import annotations
import argparse, hashlib, re, zipfile
from pathlib import Path
from prepare_build import VERSION

NAMES = ['Snap Media', 'Translation to English']
PACKAGE = 'com.app.bigtree'

def verify_bundle(bundle: Path) -> dict:
    checksum = bundle.with_name(bundle.name + '.sha256')
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    if checksum.read_text().split()[0] != digest:
        raise ValueError('BigTree bundle checksum mismatch')
    with zipfile.ZipFile(bundle) as archive:
        names = archive.namelist()
        if len(set(names)) != len(names) or archive.testzip() is not None:
            raise ValueError('Invalid MPP archive')
        manifest = archive.read('META-INF/MANIFEST.MF').decode().replace('\r\n ', '').replace('\r', '')
        for text in (f'Version: {VERSION}\n', 'Patcher-Version: 2.0.0\n', 'BigTree patches (experimental)'):
            if text not in manifest:
                raise ValueError('Unexpected MPP metadata: ' + text)
        required = 'app/morphe/patches/bigtree/BigTreePatchesKt.class'
        data = archive.read(required)
        if 'classes.dex' not in names or any(name.encode() not in data for name in NAMES):
            raise ValueError('Missing BigTree patch class, selector, or Android DEX')
        project = [name for name in names if name.startswith('app/morphe/patches/') and name.endswith('.class')]
        if not project or any(not name.startswith('app/morphe/patches/bigtree/') for name in project):
            raise ValueError('Unrelated app patches are present in BigTree bundle')
    return {'sha256': digest, 'bytes': bundle.stat().st_size, 'version': VERSION}

def verify_listing(text: str) -> None:
    names = re.findall(r'^Name: (.+)$', text, flags=re.MULTILINE)
    enabled = [v.lower() for v in re.findall(r'^Enabled: (true|false)$', text, flags=re.MULTILINE | re.IGNORECASE)]
    packages = re.findall(r'^\s*Package name: (\S+)', text, flags=re.MULTILINE)
    versions = re.findall(r'^\s+1\.14\s*$', text, flags=re.MULTILINE)
    if names != NAMES or enabled != ['false', 'false']:
        raise ValueError('BigTree selectors are missing, reordered, or enabled by default')
    if packages != [PACKAGE, PACKAGE] or len(versions) != 2:
        raise ValueError('Unexpected BigTree package/version compatibility')

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--mpp', required=True, type=Path)
    parser.add_argument('--listing', required=True, type=Path)
    args = parser.parse_args()
    print('Verified BigTree bundle:', verify_bundle(args.mpp))
    verify_listing(args.listing.read_text())
    print('Morphe lists exactly two independent BigTree 1.14 selectors')

if __name__ == '__main__':
    main()
