#!/usr/bin/env python3
"""Generate read-only 9.2.6 Hermes/native target evidence for a real remap."""
from __future__ import annotations

import io
import json
import re
import sys
import zipfile
from pathlib import Path

from androguard.core.apk import APK
from androguard.core.dex import DEX
from hermes_dec.parsers.hbc_bytecode_parser import parse_hbc_bytecode
from hermes_dec.parsers.hbc_file_parser import HBCReader
from loguru import logger

logger.remove()
source, output = map(Path, sys.argv[1:3])
root = Path(__file__).resolve().parents[2]
features = json.loads((root / "docs/simsimi/feature-gates.json").read_text())["gates"]

with zipfile.ZipFile(source) as archive:
    payload = archive.read("assets/index.android.bundle")
reader = HBCReader()
reader.read_whole_file(io.BytesIO(payload))

base_targets = [
    {"key": "membership", "function_id": 6838, "name": "getMembershipObject", "relative": 0,
     "original": "7c003701000163f27602be0e01023701000207c2510101003701000163f2bda200000001023701000163f236010103887803bc0d01032901012e01010d5c0137020004b1b57901be710201300139040105060036020406b2510202043905010506003701000163f237070107d6c736040508c36a040405080804500105026b0404013701040990f451010104aa2c02013b000301b1b53702000a21c53601000bf25403020001033602030c4c3201640101b71a53010203013700000163f25c002900012e00000d5c00"},
    {"key": "membership_events", "function_id": 6846, "name": "emitMembershipStatusChangeListener", "relative": 0,
     "original": "32017c026c00012a0100002a0101023703020163f27600bc4603003702020163f22a0102022902002e02020037020202f7dd2a0103023003390403031a00360304049a370202050bfb5303030402360203067f640101bf1a53010203015c00"},
    {"key": "ad_gate", "function_id": 6882, "name": "canShowAds", "relative": 0x18f,
     "original": "78005c00"},
    {"key": "daily_bonus", "function_id": 22097, "name": "?anon_0_", "relative": 0x13,
     "original": "3701010243f4"},
]
for gate in features:
    base_targets.append({
        "key": gate["feature"], "function_id": gate["function_id"],
        "name": gate["function_name"], "relative": gate["relative_offset"],
        "original": gate["original"],
    })

def occurrences(blob: bytes, needle: bytes):
    found, start = [], 0
    while True:
        at = blob.find(needle, start)
        if at < 0:
            return found
        found.append(at)
        start = at + 1

mapped = []
for target in base_targets:
    needle = bytes.fromhex(target["original"])
    same_id = reader.function_headers[target["function_id"]] if target["function_id"] < len(reader.function_headers) else None
    candidates = []
    for fid, header in enumerate(reader.function_headers):
        name = reader.strings[header.functionName]
        if fid == target["function_id"] or (target["name"] != "?anon_0_" and name == target["name"]):
            code = payload[header.offset:header.offset + header.bytecodeSizeInBytes]
            candidates.append({
                "function_id": fid, "name": name, "offset": header.offset,
                "size": header.bytecodeSizeInBytes, "frame_size": header.frameSize,
                "same_function_id": fid == target["function_id"],
                "needle_relative_occurrences": occurrences(code, needle),
                "bytes_at_old_relative": code[target["relative"]:target["relative"] + len(needle)].hex()
                    if target["relative"] + len(needle) <= len(code) else None,
                "disassembly": [repr(ins) for ins in parse_hbc_bytecode(header, reader)],
            })
    mapped.append({
        **target,
        "global_original_occurrences": occurrences(payload[:-20], needle),
        "candidates": candidates,
        "same_id_name": reader.strings[same_id.functionName] if same_id else None,
    })

apk = APK(str(source))
nav_classes = []
for dex_bytes in apk.get_all_dex():
    for cls in DEX(dex_bytes).get_classes():
        name = cls.get_name()
        if not name.startswith("Lcom/aurelhubert/ahbottomnavigation/"):
            continue
        methods = []
        for method in cls.get_methods():
            descriptor = method.get_descriptor()
            relevant = (
                method.get_name() == "onClick" or
                any(word in method.get_name().lower() for word in ("item", "click", "current", "update", "create")) or
                ("Landroid/view/View;" in descriptor and method.get_code() is not None)
            )
            if not relevant:
                continue
            instructions = []
            if method.get_code():
                instructions = [ins.get_name() + " " + ins.get_output() for ins in method.get_instructions()]
            methods.append({
                "name": method.get_name(), "descriptor": descriptor,
                "access": method.get_access_flags_string(), "instructions": instructions,
            })
        nav_classes.append({
            "name": name, "superclass": cls.get_superclassname(),
            "interfaces": cls.get_interfaces(), "methods": methods,
        })

extra_functions = []
for fid in (21172, 25715, 31003):
    header = reader.function_headers[fid]
    extra_functions.append({
        "function_id": fid, "name": reader.strings[header.functionName],
        "offset": header.offset, "size": header.bytecodeSizeInBytes,
        "frame_size": header.frameSize,
        "bytecode_hex": payload[header.offset:header.offset + header.bytecodeSizeInBytes].hex(),
        "disassembly": [repr(ins) for ins in parse_hbc_bytecode(header, reader)],
    })

result = {
    "source_sha256": __import__("hashlib").sha256(source.read_bytes()).hexdigest(),
    "hermes": {
        "size": len(payload), "sha256": __import__("hashlib").sha256(payload).hexdigest(),
        "function_count": len(reader.function_headers), "string_count": len(reader.strings),
        "selected_string_ids": {
            name: reader.strings.index(name) for name in
            ("Object", "assign", "currentMembershipStatus", "getMembershipObject", "hasMembership")
        },
    },
    "hermes_targets": mapped,
    "extra_functions": extra_functions,
    "bottom_navigation_classes": nav_classes,
    "scope": "Read-only candidate mapping. A target is not accepted until exact transform and patched-output verification pass.",
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
print(json.dumps({
    "hermes": result["hermes"],
    "targets": [{"key": item["key"], "old_id": item["function_id"],
                 "same_id_name": item["same_id_name"], "global_hits": item["global_original_occurrences"],
                 "candidates": [{"id": c["function_id"], "name": c["name"], "offset": c["offset"],
                                 "size": c["size"], "hits": c["needle_relative_occurrences"],
                                 "old_relative_bytes": c["bytes_at_old_relative"]} for c in item["candidates"]]
                } for item in mapped],
    "bottom_navigation_classes": len(nav_classes),
}, separators=(",", ":")))
