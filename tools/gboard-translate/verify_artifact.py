#!/usr/bin/env python3
"""Fail closed if the experimental fork does not preserve upstream metadata."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
NAME = "Direct Google Translate (experimental)"
VERSION = "4.0.0-direct-translate-dev.1"
PACKAGE = "com.google.android.inputmethod.latin"
TARGET = "18.5.4.993608717-release-arm64-v8a"


def verify(bundle: Path, metadata: Path, listing: Path) -> str:
    stock = json.loads((ROOT / "bundles/gboard/patches-list.json").read_text())
    fork = json.loads(metadata.read_text())
    if fork.get("version") != VERSION:
        raise ValueError("Unexpected fork version")
    entries = fork["patches"]
    added = [patch for patch in entries if patch["name"] == NAME]
    if len(entries) != 44 or len(added) != 1 or added[0]["use"] is not False:
        raise ValueError("Expected 43 upstream features plus one opt-in experimental patch")
    if added[0]["compatiblePackages"] != {PACKAGE: [TARGET]}:
        raise ValueError("Unexpected experimental patch compatibility")
    if [patch for patch in entries if patch["name"] != NAME] != stock["patches"]:
        raise ValueError("The 43 upstream patch entries changed")
    text = listing.read_text()
    names = re.findall(r"^Name: (.+)$", text, flags=re.MULTILINE)
    enabled = re.findall(r"^Enabled: (.+)$", text, flags=re.MULTILINE)
    if len(names) != 44 or set(names) != {patch["name"] for patch in entries} or len(enabled) != 44:
        raise ValueError("Morphe Desktop did not load exactly the expected 44 patches")
    if sum(value.lower() == "true" for value in enabled) != 43:
        raise ValueError("Unexpected Morphe defaults")
    if text.count("Package name: " + PACKAGE) != 44 or text.count(TARGET) != 44:
        raise ValueError("Unexpected Morphe target metadata")
    with zipfile.ZipFile(bundle) as archive:
        if archive.testzip() is not None:
            raise ValueError("Corrupted MPP")
        required = {"META-INF/MANIFEST.MF", "classes.dex", "extensions/gboard-patches.rve"}
        if not required.issubset(archive.namelist()):
            raise ValueError("Missing MPP payload")
        manifest = archive.read("META-INF/MANIFEST.MF").decode("utf-8").replace("\r\n ", "")
        if VERSION not in manifest or "experimental fork" not in manifest:
            raise ValueError("MPP manifest is not clearly labeled as a fork")
        if "moeunzinkh-debug/YouTube-patch-clone-" not in manifest or "Jason Wu" not in manifest:
            raise ValueError("Fork provenance or upstream attribution missing")
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    print(f"Verified experimental MPP: {bundle.stat().st_size} bytes, SHA-256 {digest}")
    print("Morphe Desktop loaded 43 unchanged upstream registrations and one opt-in experimental registration.")
    return digest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("metadata", type=Path)
    parser.add_argument("listing", type=Path)
    args = parser.parse_args()
    verify(args.bundle, args.metadata, args.listing)


if __name__ == "__main__":
    main()
