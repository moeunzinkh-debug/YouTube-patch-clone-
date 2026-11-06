#!/usr/bin/env python3
"""Make a temporary non-stock fixture with consistent manifest/resource package names.

The input is an already-patched third-party APK, not stock Gboard. Only two
fixed-length package strings are changed; no APK produced here is distributed.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/gboard-translate'))
from make_manifest_fixture import OLD, NEW, replace_manifest_package  # noqa: E402


def replace_resource_package(resource_table: bytes, old: str = OLD, new: str = NEW) -> bytes:
    data = bytearray(resource_table)
    if len(data) < 12:
        raise ValueError('Truncated resource table')
    kind, header, total, _ = struct.unpack_from('<HHII', data, 0)
    if kind != 0x0002 or header < 12 or total != len(data):
        raise ValueError('Invalid resource table header')
    cursor = header
    count = 0
    while cursor < len(data):
        if cursor + 8 > len(data):
            raise ValueError('Truncated resource table chunk')
        chunk_type, chunk_header, chunk_size = struct.unpack_from('<HHI', data, cursor)
        if chunk_header < 8 or chunk_size < chunk_header or cursor + chunk_size > len(data):
            raise ValueError('Invalid resource table chunk')
        if chunk_type == 0x0200:  # ResTable_package, name is char16_t[128] after id
            if chunk_header < 268:
                raise ValueError('Invalid resource package header')
            start = cursor + 12
            raw_name = bytes(data[start:start + 256]).decode('utf-16le')
            current = raw_name.split('\x00', 1)[0]
            if current == old:
                encoded = new.encode('utf-16le')
                if len(encoded) >= 256:
                    raise ValueError('Replacement package name is too long')
                data[start:start + 256] = encoded + bytes(256 - len(encoded))
                count += 1
        cursor += chunk_size
    if cursor != len(data) or count != 1:
        raise ValueError(f'Expected exactly one renamed resource package, found {count}')
    return bytes(data)


def create(input_apk: Path, output_apk: Path) -> None:
    if input_apk.resolve() == output_apk.resolve() or output_apk.exists():
        raise ValueError('Output must be a new file; do not overwrite an input APK')
    with zipfile.ZipFile(input_apk) as source, zipfile.ZipFile(output_apk, 'w') as destination:
        if source.namelist().count('AndroidManifest.xml') != 1 or source.namelist().count('resources.arsc') != 1:
            raise ValueError('Expected one manifest and one resource table')
        for entry in source.infolist():
            if entry.filename == 'AndroidManifest.xml':
                destination.writestr(entry, replace_manifest_package(source.read(entry)))
            elif entry.filename == 'resources.arsc':
                destination.writestr(entry, replace_resource_package(source.read(entry)))
            else:
                with source.open(entry) as src, destination.open(entry, 'w') as dst:
                    shutil.copyfileobj(src, dst, 1024 * 1024)
    print('Created a temporary unsigned fixture from a prepatched, non-stock Gboard APK.')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_apk', type=Path)
    parser.add_argument('output_apk', type=Path)
    args = parser.parse_args()
    create(args.input_apk, args.output_apk)


if __name__ == '__main__':
    main()
