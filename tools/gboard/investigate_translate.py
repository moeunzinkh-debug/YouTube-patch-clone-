#!/usr/bin/env python3
"""Inventory Translate-related DEX references, without distributing the APK.

This diagnostic needs androguard 4.1.3. It records class/method names and
public-looking Translate-related constants, not APK bytecode or user data.
"""

import argparse
import gc
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

from loguru import logger

logger.remove()
from androguard.core.apk import APK  # noqa: E402
from androguard.core.dex import DEX  # noqa: E402

TERMS = re.compile(r"translat", re.IGNORECASE)
SECRET_MARKERS = re.compile(r"(AIza[\w-]{10,}|api[_-]?key|access[_-]?token|authorization|bearer\s)", re.IGNORECASE)
DEX_NAME = re.compile(r"classes(?:[2-9]|[1-9][0-9]+)?\.dex\Z")
MAX_STRINGS = 600
MAX_METHODS_PER_STRING = 20


def safe_string(value):
    if not isinstance(value, str) or not TERMS.search(value) or SECRET_MARKERS.search(value):
        return None
    # Avoid arbitrary binary, huge configuration blobs and URLs with query parameters.
    if len(value) > 240 or any(ord(char) < 32 for char in value):
        return None
    if "?" in value and ("http://" in value or "https://" in value):
        value = value.split("?", 1)[0] + "?[redacted]"
    return value


def has_candidate(raw, targets):
    """Cheap prefilter; real instruction parsing below rejects false positives."""
    for opcode in (b"\x1a", b"\x1b"):
        pos = raw.find(opcode)
        while pos != -1:
            width = 2 if opcode == b"\x1a" else 4
            if pos % 2 == 0 and pos + 2 + width <= len(raw):
                if int.from_bytes(raw[pos + 2 : pos + 2 + width], "little") in targets:
                    return True
            pos = raw.find(opcode, pos + 1)
    return False


def method_id(method):
    return method.get_class_name() + "->" + method.get_name() + method.get_descriptor()


def inspect_dex(data, dex_name):
    dex = DEX(data)
    targets = {}
    for index in range(dex.get_len_strings()):
        value = safe_string(dex.get_cm_string(index))
        if value is not None:
            targets[index] = value
    classes = sorted(item.get_name() for item in dex.get_classes() if TERMS.search(item.get_name()))
    references = defaultdict(list)
    for method in dex.get_encoded_methods():
        code = method.get_code()
        if code is None or not has_candidate(code.get_bc().get_raw(), targets):
            continue
        instructions = list(method.get_instructions())
        matches = {
            targets[instruction.get_ref_kind()]
            for instruction in instructions
            if instruction.get_name() in ("const-string", "const-string/jumbo")
            and instruction.get_ref_kind() in targets
        }
        if not matches:
            continue
        invokes = []
        for instruction in instructions:
            if instruction.get_name().startswith("invoke-"):
                output = instruction.get_output()
                if "->" in output:
                    descriptor = output.split(", ")[-1]
                    if len(descriptor) <= 240 and not SECRET_MARKERS.search(descriptor):
                        invokes.append(descriptor)
        details = {"method": method_id(method), "invokes": list(dict.fromkeys(invokes))[:30]}
        for value in matches:
            references[value].append(details)
    ordered = sorted(set(targets.values()), key=lambda value: (value.lower(), value))
    return {
        "dex": dex_name,
        "string_count": dex.get_len_strings(),
        "matching_string_count": len(ordered),
        "matching_class_count": len(classes),
        "classes": classes[:MAX_STRINGS],
        "strings": [
            {"value": value, "reference_count": len(references[value]), "references": references[value][:MAX_METHODS_PER_STRING]}
            for value in ordered[:MAX_STRINGS]
        ],
        "truncated": len(ordered) > MAX_STRINGS or len(classes) > MAX_STRINGS,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("apk", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source", choices=("google-play", "third-party-prepatched"), required=True)
    parser.add_argument("--signer-sha256", required=True)
    args = parser.parse_args()
    apk = APK(str(args.apk))
    package = apk.get_package()
    version_name = apk.get_androidversion_name()
    version_code = str(apk.get_androidversion_code())
    if version_name != "18.5.4.993608717-release-arm64-v8a" or version_code != "176049702":
        raise SystemExit("APK does not have the expected version name and version code")
    if args.source == "google-play" and package != "com.google.android.inputmethod.latin":
        raise SystemExit("Google Play APK does not have the expected package")
    report = {
        "input": {
            "source": args.source,
            "package": package,
            "version_name": version_name,
            "version_code": version_code,
            "sha256": hashlib.file_digest(args.apk.open("rb"), "sha256").hexdigest(),
            "signing_certificate_sha256": args.signer_sha256,
            "note": "Static analysis only; the input APK is not redistributed. A third-party-prepatched APK is not an official unmodified build.",
        },
        "method": "Translate-related string constants and classes, plus verified const-string references; absence does not rule out obfuscated or native code.",
        "dex": [],
    }
    del apk
    gc.collect()
    with ZipFile(args.apk) as archive:
        names = sorted(name for name in archive.namelist() if DEX_NAME.fullmatch(name))
        if not names:
            raise SystemExit("No DEX files found in APK")
        for name in names:
            print("Inspecting", name, flush=True)
            data = archive.read(name)
            report["dex"].append(inspect_dex(data, name))
            del data
            gc.collect()
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Wrote", args.output, flush=True)


if __name__ == "__main__":
    main()
