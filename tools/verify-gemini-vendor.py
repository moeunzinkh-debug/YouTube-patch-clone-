#!/usr/bin/env python3
"""Verify the vendored Gemini / MicroG RE patch snapshot.

Checks that every file listed in extras/gemini-microg-patches/SOURCE.json is
present with the recorded SHA-256, that the JSON profiles are valid, that the
README patch tags are in sync with the Kotlin sources, and that the vendored
directory is NOT inside any Gradle source set (so `patch.mpp` stays YouTube-only).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRA = ROOT / "extras" / "gemini-microg-patches"
README = ROOT / "README.md"
EXPECTED_PATCHES = 13


def check(ok: bool, message: str) -> None:
    print(("[OK  ] " if ok else "[FAIL] ") + message)
    if not ok:
        sys.exit(1)


def main() -> None:
    prov_path = EXTRA / "SOURCE.json"
    check(prov_path.is_file(), "SOURCE.json exists")
    prov = json.loads(prov_path.read_text(encoding="utf-8"))
    check(prov.get("upstream_tag") == "v0.1.1", f"upstream tag: {prov.get('upstream_tag')}")
    check("ryuya0124/gemini-microg-patches" in prov.get("upstream", ""), "upstream URL recorded")

    listed = prov.get("files", [])
    check(len(listed) >= 19, f"{len(listed)} vendored files listed")
    for entry in listed:
        path = EXTRA / entry["path"]
        check(path.is_file(), f"present: {entry['path']}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        check(digest == entry["sha256"], f"SHA-256: {entry['path']}")

    for path in EXTRA.rglob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))
    check(True, "all vendored JSON files parse")

    kt = EXTRA / "src/main/kotlin/app/morphe/patches/google"
    names: list[str] = []
    for path in sorted(kt.rglob("*.kt")):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"name\s*=\s*\"([^\"]+)\"", text):
            before = text[max(0, match.start() - 600):match.start()]
            if "Patch(" in before or "patch(" in before:
                names.append(match.group(1))
    names = list(dict.fromkeys(names))
    check(len(names) == EXPECTED_PATCHES, f"{len(names)} patch declarations found")

    readme = README.read_text(encoding="utf-8")
    block = readme.split("<!-- GEMINI-PATCH-LIST:START -->")[1].split(
        "<!-- GEMINI-PATCH-LIST:END -->")[0]
    missing = [name for name in names if f"`{name}`" not in block]
    check(not missing, f"README tags list all patches (missing: {missing})")
    check(block.count("<details>") == block.count("</details>"), "README <details> tags balanced")
    check(block.count("<summary>") == block.count("</summary>"), "README <summary> tags balanced")

    # The vendored snapshot must stay out of the compiled bundle.
    settings = (ROOT / "settings.gradle.kts").read_text(encoding="utf-8")
    check("extras" not in settings, "extras/ is not registered as a Gradle module")
    build_files = list(ROOT.rglob("*.gradle.kts"))
    leak = [str(p.relative_to(ROOT)) for p in build_files
            if "extras/gemini-microg-patches" in p.read_text(encoding="utf-8")]
    check(not leak, f"no Gradle file references the vendored sources ({leak})")

    # The compiled bundle must not contain Gemini/Google patch classes.
    from zipfile import ZipFile
    with ZipFile(ROOT / "patch.mpp") as archive:
        classes = [n for n in archive.namelist() if n.endswith(".class")]
    gemini = [n for n in classes if n.startswith("app/morphe/patches/google/")]
    check(not gemini, f"patch.mpp has no Gemini patch classes ({gemini[:3]})")

    print("\nGemini / MicroG RE vendored snapshot is valid.")


if __name__ == "__main__":
    main()
