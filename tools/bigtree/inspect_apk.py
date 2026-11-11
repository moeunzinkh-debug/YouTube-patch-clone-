#!/usr/bin/env python3
"""Read-only inventory of the exact uploaded BigTree APK."""
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
EXPECTED = "51b7b05b0171d0f242b37933af8c570dae50b6da3b33a0bfa7dce5814c08977a"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

if sha(source.read_bytes()) != EXPECTED:
    raise SystemExit("Unexpected BigTree APK")
apk = APK(str(source))

certificates = set()
for getter in ("get_certificates_der_v3", "get_certificates_der_v2", "get_certificates_der_v1"):
    method = getattr(apk, getter, None)
    if method:
        try:
            certificates.update(sha(cert) for cert in method())
        except Exception:
            pass

terms = re.compile(
    r"snap|media|translat|english|language|locale|caption|subtitle|photo|image|video|"
    r"camera|gallery|download|share|clipboard|ocr|speech|audio",
    re.I,
)
urls = re.compile(rb"https?://[^\x00-\x20\"'<>]{4,240}")
classes = []
string_matches = set()
url_matches = set()
all_class_count = 0
all_method_count = 0
with zipfile.ZipFile(source) as archive:
    names = archive.namelist()
    dex_names = [name for name in names if re.fullmatch(r"classes\d*\.dex", name)]
    native = [name for name in names if name.startswith("lib/") and name.endswith(".so")]
    assets = [name for name in names if name.startswith("assets/")]
    interesting_entries = [name for name in names if terms.search(name)]
    for name in names:
        if name.endswith("/"):
            continue
        try:
            data = archive.read(name)
        except Exception:
            continue
        if len(data) <= 8 * 1024 * 1024:
            text = data.decode("utf-8", errors="ignore")
            for match in re.finditer(r"[^\r\n\x00]{0,100}(?:snap|media|translat|english|language|caption|subtitle|ocr)[^\r\n\x00]{0,140}", text, re.I):
                value = match.group(0).strip()
                if value:
                    string_matches.add(value[:400])
            for value in urls.findall(data):
                url_matches.add(value.decode("utf-8", errors="replace")[:300])
    for dex_name in dex_names:
        dex = DEX(archive.read(dex_name))
        for cls in dex.get_classes():
            all_class_count += 1
            name = cls.get_name()
            methods = []
            relevant_class = bool(terms.search(name)) or name.startswith("L" + apk.get_package().replace(".", "/") + "/")
            for method in cls.get_methods():
                all_method_count += 1
                method_relevant = relevant_class or bool(terms.search(method.get_name()))
                if not method_relevant:
                    continue
                item = {
                    "name": method.get_name(),
                    "descriptor": method.get_descriptor(),
                    "access": method.get_access_flags_string(),
                }
                if method.get_code() and (terms.search(method.get_name()) or relevant_class):
                    instructions = [ins.get_name() + " " + ins.get_output() for ins in method.get_instructions()]
                    references = [line for line in instructions if terms.search(line) or "const-string" in line or "invoke-" in line]
                    if references:
                        item["relevant_instructions"] = references[:300]
                methods.append(item)
            if methods:
                classes.append({
                    "name": name,
                    "superclass": cls.get_superclassname(),
                    "interfaces": cls.get_interfaces(),
                    "methods": methods,
                })

report = {
    "source": {"filename": source.name, "sha256": EXPECTED, "bytes": source.stat().st_size},
    "metadata": {
        "package": apk.get_package(),
        "version_name": apk.get_androidversion_name(),
        "version_code": apk.get_androidversion_code(),
        "min_sdk": apk.get_min_sdk_version(),
        "target_sdk": apk.get_target_sdk_version(),
        "main_activity": apk.get_main_activity(),
        "application": apk.get_attribute_value("application", "name"),
        "permissions": sorted(apk.get_permissions()),
        "activities": sorted(apk.get_activities()),
        "services": sorted(apk.get_services()),
        "receivers": sorted(apk.get_receivers()),
    },
    "signing_certificate_sha256": sorted(certificates),
    "archive": {
        "entry_count": len(names), "dex_files": dex_names, "native_libraries": native,
        "assets": assets, "interesting_entry_names": interesting_entries,
        "has_flutter_assets": any("flutter_assets" in name for name in names),
        "has_flutter_libapp": any(name.endswith("/libapp.so") for name in names),
        "has_react_native_bundle": any(name.endswith("index.android.bundle") for name in names),
    },
    "dex": {"class_count": all_class_count, "method_count": all_method_count, "relevant_classes": classes},
    "interesting_strings": sorted(string_matches)[:2000],
    "urls": sorted(url_matches)[:1000],
    "scope": "Read-only static inventory; no feature behavior or patchability is claimed.",
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
print(json.dumps({
    "metadata": report["metadata"],
    "certificate": report["signing_certificate_sha256"],
    "archive": {k: report["archive"][k] for k in ("entry_count", "dex_files", "native_libraries", "has_flutter_assets", "has_flutter_libapp", "has_react_native_bundle")},
    "relevant_class_count": len(classes),
    "interesting_string_count": len(report["interesting_strings"]),
    "url_count": len(report["urls"]),
}, ensure_ascii=False, separators=(",", ":")))
