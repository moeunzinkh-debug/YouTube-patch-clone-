#!/usr/bin/env python3
"""Emit exact focused DEX evidence for BigTree feature target selection."""
from __future__ import annotations
import hashlib, json, re, sys, zipfile
from pathlib import Path
from androguard.core.apk import APK
from androguard.core.dex import DEX
from loguru import logger
logger.remove()
source, output = map(Path, sys.argv[1:3])
EXPECTED = "51b7b05b0171d0f242b37933af8c570dae50b6da3b33a0bfa7dce5814c08977a"
if hashlib.sha256(source.read_bytes()).hexdigest() != EXPECTED:
    raise SystemExit("Unexpected BigTree APK")
apk = APK(str(source))

def safe_annotations(item):
    try:
        value = item.get_annotations()
        return [str(v) for v in value]
    except Exception:
        return []

def method_record(method):
    code = method.get_code()
    return {
        "name": method.get_name(), "descriptor": method.get_descriptor(),
        "access": method.get_access_flags_string(), "annotations": safe_annotations(method),
        "registers": code.get_registers_size() if code else None,
        "instructions": [ins.get_name() + (" " + ins.get_output() if ins.get_output() else "") for ins in method.get_instructions()] if code else [],
    }

with zipfile.ZipFile(source) as archive:
    dex = DEX(archive.read("classes.dex"))
    classes = list(dex.get_classes())
    by_name = {c.get_name(): c for c in classes}
    roots = {"Lcom/app/bigtree/App;", "Lcom/app/bigtree/MainActivity;", "LG1/I;", "LB/n;"}
    # Include obfuscated first-party classes directly referenced by root bytecode.
    reference_pattern = re.compile(r"L(?:G1|com/app/bigtree)/[^;]+;")
    referenced = set()
    for name in roots:
        for method in by_name[name].get_methods():
            for ins in method.get_instructions():
                referenced.update(reference_pattern.findall(ins.get_output()))
    selected = roots | referenced
    records = []
    for name in sorted(selected):
        cls = by_name.get(name)
        if not cls:
            continue
        records.append({
            "name": name, "superclass": cls.get_superclassname(), "interfaces": cls.get_interfaces(),
            "annotations": safe_annotations(cls),
            "fields": [{
                "name": f.get_name(), "type": f.get_descriptor(), "access": f.get_access_flags_string(),
                "value": str(f.get_init_value()), "annotations": safe_annotations(f),
            } for f in cls.get_fields()],
            "methods": [method_record(m) for m in cls.get_methods()],
        })
    string_values = sorted({str(s.get_value() if hasattr(s, "get_value") else s) for s in dex.get_strings()})
    feature_strings = [s for s in string_values if re.search(
        r"snap|translat|english|locale|language|media|photo|image|video|camera|gallery|download|bridge|javascript|header|config|route|feature|flag",
        s, re.I)]
report = {
    "source_sha256": EXPECTED,
    "package": apk.get_package(), "version_name": apk.get_androidversion_name(), "version_code": apk.get_androidversion_code(),
    "selection": "App, MainActivity, Android JavaScript bridge, and their directly referenced first-party classes",
    "classes": records,
    "feature_strings": feature_strings,
    "scope": "Static DEX targeting evidence only; no runtime behavior is claimed.",
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"selected_classes": len(records), "feature_strings": len(feature_strings), "output_bytes": output.stat().st_size}))
