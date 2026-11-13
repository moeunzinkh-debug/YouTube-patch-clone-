#!/usr/bin/env python3
"""Verify the standalone Pingo AI MPP and exact selector listing."""
from __future__ import annotations
import argparse, hashlib, re, zipfile
from pathlib import Path
from prepare_build import VERSION

NAMES = ['Remove license check', 'Unlock all feature']
PACKAGE = 'com.picoai.languageapp.android'
VERSION_NAME = '5.4.8'

def verify_bundle(bundle: Path) -> dict:
    checksum = bundle.with_name(bundle.name + '.sha256')
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    if checksum.read_text().split()[0] != digest:
        raise ValueError('Pingo bundle checksum mismatch')
    with zipfile.ZipFile(bundle) as archive:
        names = archive.namelist()
        if len(set(names)) != len(names) or archive.testzip() is not None:
            raise ValueError('Invalid MPP archive')
        manifest = archive.read('META-INF/MANIFEST.MF').decode().replace('\r\n ', '').replace('\r', '')
        for text in (f'Version: {VERSION}\n', 'Patcher-Version: 2.0.0\n', 'Pingo AI patches (experimental)'):
            if text not in manifest:
                raise ValueError('Unexpected MPP metadata: ' + text)
        required = 'app/morphe/patches/pingo/PingoPatchesKt.class'
        data = archive.read(required)
        if 'classes.dex' not in names or any(name.encode() not in data for name in NAMES):
            raise ValueError('Missing Pingo patch class, selector, or Android DEX')
        project = [name for name in names if name.startswith('app/morphe/patches/') and name.endswith('.class')]
        if not project or any(not name.startswith('app/morphe/patches/pingo/') for name in project):
            raise ValueError('Unrelated app patches are present in Pingo bundle')
    return {'sha256': digest, 'bytes': bundle.stat().st_size, 'version': VERSION}

def verify_listing(text: str) -> None:
    names = re.findall(r'^Name: (.+)$', text, flags=re.MULTILINE)
    enabled = [v.lower() for v in re.findall(r'^Enabled: (true|false)$', text, flags=re.MULTILINE | re.IGNORECASE)]
    packages = re.findall(r'^\s*Package name: (\S+)', text, flags=re.MULTILINE)
    versions = re.findall(r'^\s+5\.4\.8\s*$', text, flags=re.MULTILINE)
    if names != NAMES or enabled != ['false', 'false']:
        raise ValueError('Pingo selectors are missing, reordered, or enabled by default')
    if packages != [PACKAGE, PACKAGE] or len(versions) != 2:
        raise ValueError('Unexpected Pingo package/version compatibility')

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--mpp', required=True, type=Path)
    parser.add_argument('--listing', required=True, type=Path)
    args = parser.parse_args()
    print('Verified Pingo bundle:', verify_bundle(args.mpp))
    verify_listing(args.listing.read_text())
    print('Morphe lists exactly two independent Pingo AI 5.4.8 selectors')

if __name__ == '__main__':
    main()
