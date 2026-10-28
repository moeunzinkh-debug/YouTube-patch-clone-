#!/usr/bin/env python3
"""Make a non-installable test fixture from the pinned *prepatched* APK.

Only the binary manifest's package-name string is changed, in place. This lets
Morphe select the real fork MPP against the renamed third-party sample. The
optional --restore mode uses the original padded slot to restore the third-party
package solely for emulator isolation. Neither mode produces a stock APK or a
distributable app.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import struct
import zipfile

OLD = "dev.jason.com.google.android.inputmethod.latin"
NEW = "com.google.android.inputmethod.latin"


def u16(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def length8(data: bytes | bytearray, offset: int) -> tuple[int, int]:
    first = data[offset]
    return (((first & 0x7F) << 8) | data[offset + 1], offset + 2) if first & 0x80 else (first, offset + 1)


def length16(data: bytes | bytearray, offset: int) -> tuple[int, int]:
    first = u16(data, offset)
    return (((first & 0x7FFF) << 16) | u16(data, offset + 2), offset + 4) if first & 0x8000 else (first, offset + 2)


def replace_manifest_package(manifest: bytes, old: str = OLD, new: str = NEW) -> bytes:
    data = bytearray(manifest)
    if len(data) < 8 or u16(data, 0) != 3 or u32(data, 4) != len(data):
        raise ValueError("Invalid Android binary XML header")
    cursor = u16(data, 2)
    matches = 0
    while cursor + 8 <= len(data):
        kind, header_size, size = struct.unpack_from("<HHI", data, cursor)
        if size < header_size or size < 8 or cursor + size > len(data):
            raise ValueError("Invalid binary XML chunk")
        if kind == 1:  # ResStringPool_header
            if header_size < 28:
                raise ValueError("Invalid string pool header")
            count, flags, strings_start = u32(data, cursor + 8), u32(data, cursor + 16), u32(data, cursor + 20)
            if cursor + header_size + count * 4 > cursor + size or strings_start >= size:
                raise ValueError("Invalid string pool offsets")
            utf8 = bool(flags & 0x100)
            offsets = [u32(data, cursor + header_size + 4 * index) for index in range(count)]
            styles_start = u32(data, cursor + 24)
            pool_end = cursor + (styles_start if styles_start else size)
            for index in range(count):
                position = cursor + strings_start + offsets[index]
                later = [cursor + strings_start + value for value in offsets if value > offsets[index]]
                boundary = min(later, default=pool_end)
                if not cursor <= position < boundary <= cursor + size:
                    raise ValueError("Invalid string position")
                if utf8:
                    _, pos = length8(data, position)
                    byte_length, pos = length8(data, pos)
                    end = pos + byte_length
                    if end >= cursor + size or data[end] != 0:
                        raise ValueError("Invalid UTF-8 pool string")
                    value = bytes(data[pos:end]).decode("utf-8")
                    if value == old:
                        encoded = new.encode("utf-8")
                        units = len(new.encode("utf-16le")) // 2
                        if len(encoded) >= 128 or units >= 128:
                            raise ValueError("Unexpected replacement length")
                        replacement = bytes([units, len(encoded)]) + encoded + b"\0"
                    else:
                        continue
                else:
                    units, pos = length16(data, position)
                    end = pos + units * 2
                    if end + 2 > cursor + size or data[end:end + 2] != b"\0\0":
                        raise ValueError("Invalid UTF-16 pool string")
                    value = bytes(data[pos:end]).decode("utf-16le")
                    if value == old:
                        encoded = new.encode("utf-16le")
                        replacement = struct.pack("<H", len(encoded) // 2) + encoded + b"\0\0"
                    else:
                        continue
                original_span = end + (1 if utf8 else 2) - position
                span = max(original_span, len(replacement))
                if position + span > boundary or boundary > pool_end:
                    raise ValueError("Replacement must fit without shifting offsets")
                if any(data[position + original_span:position + span]):
                    raise ValueError("Replacement would overwrite non-padding bytes")
                data[position:position + span] = replacement + b"\0" * (span - len(replacement))
                matches += 1
        cursor += size
    if cursor != len(data) or matches != 1:
        raise ValueError(f"Expected exactly one package string, found {matches}")
    return bytes(data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_apk", type=Path)
    parser.add_argument("output_apk", type=Path)
    parser.add_argument("--restore", action="store_true", help="restore the third-party package name for emulator isolation")
    args = parser.parse_args()
    if args.input_apk.resolve() == args.output_apk.resolve() or args.output_apk.exists():
        raise SystemExit("Use a new output path; never overwrite the input APK")
    with zipfile.ZipFile(args.input_apk) as source, zipfile.ZipFile(args.output_apk, "w") as destination:
        names = source.namelist()
        if names.count("AndroidManifest.xml") != 1:
            raise ValueError("Expected exactly one manifest")
        for entry in source.infolist():
            if entry.filename == "AndroidManifest.xml":
                before, after = (NEW, OLD) if args.restore else (OLD, NEW)
                destination.writestr(entry, replace_manifest_package(source.read(entry), before, after))
            else:
                with source.open(entry) as src, destination.open(entry, "w") as dst:
                    shutil.copyfileobj(src, dst, 1024 * 1024)
    print("Created unsigned package-renamed test fixture from third-party patched APK; NOT a stock APK.")


if __name__ == "__main__":
    main()
