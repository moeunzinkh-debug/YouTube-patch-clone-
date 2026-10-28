#!/usr/bin/env python3
"""Assemble a test-only hybrid APK: original third-party resources + Morphe-patched DEX.

This intentionally restores the prepatched sample's original renamed package so
it can coexist with the emulator's Google-signed system Gboard. It is not stock,
not an APK for distribution, and must be aligned and signed separately.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import shutil
import zipfile

DEX = re.compile(r"classes(?:[2-9]|[1-9][0-9]+)?\.dex\Z")
SIGNATURE = re.compile(r"META-INF/[^/]+\.(?:SF|RSA|DSA|EC)\Z", re.IGNORECASE)


def build(original: Path, patched: Path, output: Path) -> int:
    if output.exists() or output.resolve() in (original.resolve(), patched.resolve()):
        raise ValueError("Output must be a new file")
    with zipfile.ZipFile(original) as source, zipfile.ZipFile(patched) as result:
        names = result.namelist()
        dexes = [entry for entry in result.infolist() if DEX.fullmatch(entry.filename)]
        if not dexes or len({entry.filename for entry in dexes}) != len(dexes) or "classes.dex" not in names:
            raise ValueError("Missing or duplicate patched DEX files")
        with zipfile.ZipFile(output, "w") as destination:
            for entry in source.infolist():
                if DEX.fullmatch(entry.filename) or SIGNATURE.fullmatch(entry.filename):
                    continue
                with source.open(entry) as src, destination.open(entry, "w") as dst:
                    shutil.copyfileobj(src, dst, 1024 * 1024)
            for entry in dexes:
                with result.open(entry) as src, destination.open(entry, "w") as dst:
                    shutil.copyfileobj(src, dst, 1024 * 1024)
    return len(dexes)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_third_party_apk", type=Path)
    parser.add_argument("morphe_patched_apk", type=Path)
    parser.add_argument("output_apk", type=Path)
    args = parser.parse_args()
    count = build(args.original_third_party_apk, args.morphe_patched_apk, args.output_apk)
    print(f"Created non-stock test-only hybrid with {count} Morphe-patched DEX files; signature is invalid until re-signed.")


if __name__ == "__main__":
    main()
