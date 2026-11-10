#!/usr/bin/env python3
"""Read-only SimSimi 9.2.6 comparison against pinned 9.2.3 evidence."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

from androguard.core.apk import APK
from androguard.core.dex import DEX
from loguru import logger

logger.remove()
source, output = map(Path, sys.argv[1:3])
root = Path(__file__).resolve().parents[2]
old_targets = json.loads((root / "docs/simsimi/target-map.json").read_text())
old_navigation = json.loads((root / "docs/simsimi/quick-return-navigation.json").read_text())

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

apk = APK(str(source))
metadata = {
    "package": apk.get_package(),
    "version_name": apk.get_androidversion_name(),
    "version_code": apk.get_androidversion_code(),
    "min_sdk": apk.get_min_sdk_version(),
    "target_sdk": apk.get_target_sdk_version(),
    "main_activity": apk.get_main_activity(),
    "split": apk.get_attribute_value("manifest", "split"),
    "splits_required": apk.get_attribute_value("application", "isSplitRequired"),
}
if metadata["package"] != "com.ismaker.android.simsimi" or metadata["version_name"] != "9.2.6":
    raise SystemExit(f"Unexpected APK metadata: {metadata}")

with zipfile.ZipFile(source) as archive:
    names = archive.namelist()
    payload = archive.read("assets/index.android.bundle")
    tracked_assets = []
    for old in old_targets["asset_bundles"]:
        name = old["name"]
        if name not in names:
            tracked_assets.append({"name": name, "status": "missing", "old_sha256": old["sha256"]})
            continue
        data = archive.read(name)
        digest = sha(data)
        tracked_assets.append({
            "name": name, "status": "unchanged" if digest == old["sha256"] else "changed",
            "old_size": old["size"], "new_size": len(data),
            "old_sha256": old["sha256"], "new_sha256": digest,
        })
    archive_summary = {
        "entry_count": len(names),
        "dex_files": [name for name in names if re.fullmatch(r"classes\d*\.dex", name)],
        "native_libraries": [name for name in names if name.startswith("lib/") and name.endswith(".so")],
        "tracked_923_assets": tracked_assets,
    }

certificates = set()
for getter in ("get_certificates_der_v3", "get_certificates_der_v2", "get_certificates_der_v1"):
    method = getattr(apk, getter, None)
    if method:
        try:
            certificates.update(sha(cert) for cert in method())
        except Exception:
            pass

class_defs = {}
for dex_bytes in apk.get_all_dex():
    for cls in DEX(dex_bytes).get_classes():
        class_defs[cls.get_name()] = cls

def signatures(cls):
    return sorted(method.get_name() + method.get_descriptor() for method in cls.get_methods())

old_app = {item["name"]: item for item in old_targets["app_classes"]}
app_comparison = []
for name, old in old_app.items():
    cls = class_defs.get(name)
    if cls is None:
        app_comparison.append({"name": name, "status": "missing"})
        continue
    current = signatures(cls)
    expected = sorted(old["methods"])
    app_comparison.append({
        "name": name,
        "status": "unchanged_signatures" if current == expected and cls.get_superclassname() == old["super"] else "changed",
        "old_super": old["super"], "new_super": cls.get_superclassname(),
        "added_methods": sorted(set(current) - set(expected)),
        "removed_methods": sorted(set(expected) - set(current)),
    })

old_nav = {item["name"]: item for item in old_navigation["classes"]}
navigation = []
for name in ("Lcom/aurelhubert/ahbottomnavigation/a;", "Lcom/aurelhubert/ahbottomnavigation/b;", "Lcom/aurelhubert/ahbottomnavigation/i;"):
    cls = class_defs.get(name)
    if cls is None:
        navigation.append({"name": name, "status": "missing"})
        continue
    old = old_nav.get(name, {})
    old_methods = {method["name"] + method["descriptor"]: method for method in old.get("methods", [])}
    method_results = []
    for method in cls.get_methods():
        key = method.get_name() + method.get_descriptor()
        if key not in old_methods:
            continue
        item = {"signature": key, "status": "signature_present"}
        if "instructions" in old_methods[key] and method.get_code():
            actual = [ins.get_name() + " " + ins.get_output() for ins in method.get_instructions()]
            item["instructions_unchanged"] = actual == old_methods[key]["instructions"]
        method_results.append(item)
    navigation.append({
        "name": name,
        "status": "present",
        "superclass": cls.get_superclassname(),
        "all_old_signatures_present": set(old_methods).issubset(set(signatures(cls))),
        "methods": method_results,
    })

main = class_defs.get("Lcom/ismaker/android/simsimi/MainActivity;")
main_activity = None if main is None else {
    "superclass": main.get_superclassname(),
    "methods": signatures(main),
    "declares_dispatchTouchEvent": any(method.get_name() == "dispatchTouchEvent" for method in main.get_methods()),
}

report = {
    "scope": "Static comparison to committed 9.2.3 evidence; no device/runtime or server behavior claim.",
    "source": {
        "filename": source.name,
        "sha256": sha(source.read_bytes()),
        "bytes": source.stat().st_size,
    },
    "metadata": metadata,
    "signing_certificate_sha256": sorted(certificates),
    "hermes": {
        "size": len(payload), "sha256": sha(payload), "header_hex": payload[:40].hex(),
        "same_as_9.2.3": len(payload) == 26008892 and sha(payload) == "203256d3824cfbc449d110fca1601095ecf283f555079407d03a2f46ca0c7489",
    },
    "archive": archive_summary,
    "documented_app_class_comparison": app_comparison,
    "navigation_comparison": navigation,
    "main_activity": main_activity,
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
summary = {
    "metadata": metadata,
    "source_sha256": report["source"]["sha256"],
    "certificate_sha256": report["signing_certificate_sha256"],
    "hermes": report["hermes"],
    "tracked_assets": {item["status"]: sum(x["status"] == item["status"] for x in tracked_assets) for item in tracked_assets},
    "documented_app_classes": {status: sum(x["status"] == status for x in app_comparison) for status in sorted({x["status"] for x in app_comparison})},
    "main_activity": main_activity,
    "navigation": navigation,
}
print("SIMSIMI_926_REPORT=" + json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
