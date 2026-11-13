#!/usr/bin/env python3
"""Inspect the exact Pingo AI pre-release APK without executing or redistributing it."""
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
EXPECTED_SHA256 = "1ef37fd47d97dae52318ea0a084652d375bccc277e394ab298ab9014234a1c57"
EXPECTED_SIZE = 72566868
DEX_NAME = re.compile(r"classes(?:[2-9]|[1-9][0-9]+)?\.dex\Z")
PAIRIP = re.compile(r"Lcom/pairip/(?:application|licensecheck)/")
ENTITLEMENT = re.compile(
    r"premium|subscription|subscribe|paywall|purchase|billing|entitle|pro(?:$|[^a-z])|vip|trial|credit|quota|limit|unlock|feature.?flag",
    re.I,
)
SENSITIVE = re.compile(r"https?://|token|secret|password|credential|api.?key|bearer|private.?key|@[a-z0-9]", re.I)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_string(value: str) -> bool:
    return 1 < len(value) <= 100 and value.isprintable() and "\n" not in value and not SENSITIVE.search(value)


def method_record(method) -> dict:
    code = method.get_code()
    return {
        "name": method.get_name(),
        "descriptor": re.sub(r"\s+", "", method.get_descriptor()),
        "access": method.get_access_flags_string(),
        "registers": code.get_registers_size() if code else None,
        "instructions": [
            ins.get_name() + ((" " + ins.get_output()) if ins.get_output() else "")
            for ins in method.get_instructions()
        ] if code else [],
    }


def inspect(source: Path) -> dict:
    if source.stat().st_size != EXPECTED_SIZE or digest(source) != EXPECTED_SHA256:
        raise ValueError("Not the exact Pingo AI pre-release asset")
    apk = APK(str(source))
    if not apk.is_valid_APK():
        raise ValueError("Invalid Pingo APK")
    pairip_classes = []
    candidates = []
    safe_entitlement_strings = set()
    dex_files = []
    class_count = method_count = 0
    with zipfile.ZipFile(source) as archive:
        names = archive.namelist()
        native_libraries = sorted(n for n in names if n.startswith("lib/") and n.endswith(".so"))
        assets = sorted(n for n in names if n.startswith("assets/"))
        for info in archive.infolist():
            if not DEX_NAME.fullmatch(info.filename):
                continue
            dex_files.append({"name": info.filename, "bytes": info.file_size})
            dex = DEX(archive.read(info))
            class_count += len(dex.get_classes())
            for value in dex.get_strings():
                if isinstance(value, str) and ENTITLEMENT.search(value) and safe_string(value):
                    safe_entitlement_strings.add(value)
            for cls in dex.get_classes():
                class_name = cls.get_name()
                methods = list(cls.get_methods())
                method_count += len(methods)
                if PAIRIP.search(class_name):
                    pairip_classes.append({
                        "dex": info.filename,
                        "name": class_name,
                        "superclass": cls.get_superclassname(),
                        "methods": [method_record(m) for m in methods],
                    })
                    continue
                class_signal = bool(ENTITLEMENT.search(class_name))
                for method in methods:
                    code = method.get_code()
                    if not code:
                        continue
                    outputs = [ins.get_output() for ins in method.get_instructions()]
                    string_hits = sorted({
                        match.group(0) for output in outputs
                        for match in ENTITLEMENT.finditer(output)
                    })
                    if class_signal or ENTITLEMENT.search(method.get_name()) or string_hits:
                        candidates.append({
                            "dex": info.filename,
                            "class": class_name,
                            "method": method.get_name(),
                            "descriptor": re.sub(r"\s+", "", method.get_descriptor()),
                            "access": method.get_access_flags_string(),
                            "signals": string_hits[:20],
                            "instruction_count": sum(1 for _ in method.get_instructions()),
                        })
        framework = {
            "flutter_assets": any(n.startswith("assets/flutter_assets/") for n in names),
            "flutter_engine": any(n.endswith("/libflutter.so") for n in native_libraries),
            "flutter_app_aot": any(n.endswith("/libapp.so") for n in native_libraries),
            "react_native_bundle": any(n.endswith("index.android.bundle") for n in names),
        }
    return {
        "source": {
            "release_tag": "Pingo", "asset_id": 742911905, "filename": source.name,
            "bytes": EXPECTED_SIZE, "sha256": EXPECTED_SHA256,
        },
        "metadata": {
            "package": apk.get_package(), "version_name": apk.get_androidversion_name(),
            "version_code": apk.get_androidversion_code(), "min_sdk": apk.get_min_sdk_version(),
            "target_sdk": apk.get_target_sdk_version(), "application": apk.get_attribute_value("application", "name"),
            "main_activity": apk.get_main_activity(),
            "license_billing_integrity_permissions": sorted(p for p in apk.get_permissions()
                if re.search(r"LICENSE|BILLING|INTEGRITY|VENDING", p, re.I)),
        },
        "archive": {
            "entry_count": len(names), "dex_files": dex_files, "native_libraries": native_libraries,
            "asset_count": len(assets), "framework": framework,
        },
        "dex": {"class_count": class_count, "method_count": method_count},
        "pairip_classes": pairip_classes,
        "entitlement_candidate_count": len(candidates),
        "entitlement_candidates": candidates[:500],
        "safe_entitlement_strings": sorted(safe_entitlement_strings)[:500],
        "limits": {
            "static_only": True,
            "candidate_names_are_not_proof": True,
            "server_entitlements_and_native_or_dart_aot_logic_are_not_unlocked_by_dex_string_matches": True,
        },
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: inspect_apk.py INPUT.apk OUTPUT.json")
    output = Path(sys.argv[2])
    report = inspect(Path(sys.argv[1]))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "metadata": report["metadata"], "framework": report["archive"]["framework"],
        "pairip_classes": len(report["pairip_classes"]),
        "entitlement_candidates": report["entitlement_candidate_count"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
