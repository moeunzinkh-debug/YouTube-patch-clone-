#!/usr/bin/env python3
"""Publish compact inspection findings as API-readable GitHub annotations."""
import json
import re
import sys
from pathlib import Path

report_path, patch_log_path = map(Path, sys.argv[1:3])

def command(level, title, value):
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":")) if not isinstance(value, str) else value
    text = text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::{level} title={title}::{text}")

if report_path.exists():
    report = json.loads(report_path.read_text())
    assets = report["archive"]["tracked_923_assets"]
    classes = report["documented_app_class_comparison"]
    finding = {
        "metadata": report["metadata"],
        "source": report["source"],
        "signing_certificate_sha256": report["signing_certificate_sha256"],
        "hermes": report["hermes"],
        "tracked_assets": {
            "unchanged": [item["name"] for item in assets if item["status"] == "unchanged"],
            "changed": [item["name"] for item in assets if item["status"] == "changed"],
            "missing": [item["name"] for item in assets if item["status"] == "missing"],
        },
        "documented_app_classes": {
            "unchanged": [item["name"] for item in classes if item["status"] == "unchanged_signatures"],
            "changed_or_missing": [item for item in classes if item["status"] != "unchanged_signatures"],
        },
        "main_activity": report["main_activity"],
        "navigation": report["navigation_comparison"],
    }
    command("notice", "SimSimi 9.2.6 static comparison", finding)
else:
    command("error", "SimSimi 9.2.6 static comparison", "report.json was not produced")

if patch_log_path.exists():
    lines = patch_log_path.read_text(errors="replace").splitlines()
    pattern = re.compile(r"exception|error|failed|failure|unsupported|caused by", re.I)
    selected = [line.strip() for line in lines if pattern.search(line)]
    command("warning" if selected else "notice", "SimSimi 9.2.6 Morphe result", selected[-30:] or lines[-15:])
else:
    command("error", "SimSimi 9.2.6 Morphe result", "patch.log was not produced")
