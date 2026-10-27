#!/usr/bin/env python3
"""Regenerate the Gemini/MicroG RE `<details>` patch tags in README.md.

The patch list is read from the vendored Kotlin sources in
`extras/gemini-microg-patches/src/main/kotlin`, so a new upstream snapshot is
reflected automatically. Run from the repository root:

    python3 tools/generate-gemini-catalog.py

Everything between <!-- GEMINI-PATCH-LIST:START --> and
<!-- GEMINI-PATCH-LIST:END --> is replaced; the rest of the README is untouched.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRA = ROOT / "extras" / "gemini-microg-patches"
README = ROOT / "README.md"
START = "<!-- GEMINI-PATCH-LIST:START -->"
END = "<!-- GEMINI-PATCH-LIST:END -->"

# Directory (under .../patches/google/) -> display group. Order matters.
GROUPS: list[tuple[str, str]] = [
    ("microg", "🔐 MicroG RE / GmsCore"),
    ("gemini", "🤖 Gemini launcher"),
    ("clone", "📦 Google App clone"),
    ("workprofile", "💼 Work profile / Secure Folder"),
    ("account", "👤 Account sync (off by default)"),
    ("common", "🧩 Version hook registry"),
]

# Files that live in a directory whose name is misleading for grouping.
CLONE_FILES = {"GoogleAppCloneFixPatch.kt", "ProcessNameSanitizePatch.kt"}


def patches() -> list[dict]:
    found: list[dict] = []
    src = EXTRA / "src" / "main" / "kotlin" / "app" / "morphe" / "patches" / "google"
    for path in sorted(src.rglob("*.kt")):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"name\s*=\s*\"([^\"]+)\"", text):
            # Only patch declarations (bytecodePatch / resourcePatch / rawResourcePatch).
            before = text[max(0, match.start() - 600):match.start()]
            if "Patch(" not in before and "patch(" not in before:
                continue
            window = text[match.start():match.start() + 1200]
            default = re.search(r"default\s*=\s*(true|false)", window)
            compatible = re.search(r"compatibleWith\(\"([^\"]+)\"\)", window)
            if path.name in CLONE_FILES:
                group = "📦 Google App clone"
            else:
                group = next(
                    (title for folder, title in GROUPS if f"/{folder}/" in str(path)),
                    "🧩 Other",
                )
            found.append({
                "name": match.group(1),
                "default": (default.group(1) == "true") if default else True,
                "package": compatible.group(1) if compatible else "",
                "group": group,
                "file": str(path.relative_to(ROOT)),
            })
    # de-duplicate while keeping order
    seen: set[str] = set()
    unique = []
    for item in found:
        if item["name"] not in seen:
            seen.add(item["name"])
            unique.append(item)
    return unique


def main() -> None:
    prov = json.loads((EXTRA / "SOURCE.json").read_text(encoding="utf-8"))
    items = patches()
    if not items:
        raise SystemExit("No Gemini patches found in the vendored sources")

    order = [title for _, title in GROUPS] + ["🧩 Other"]
    buckets: dict[str, list[dict]] = {g: [] for g in order}
    for item in items:
        buckets.setdefault(item["group"], []).append(item)

    lines: list[str] = [
        START,
        "<details>",
        f"<summary>🤖 Gemini / MicroG RE • {len(items)} patches (vendored v{prov['upstream_bundle_version']}, separate source)</summary>",
        "",
        "### Gemini patch tags / ស្លាក patch សម្រាប់ Gemini",
        "",
        "Cloned from [ryuya0124/gemini-microg-patches]"
        "(https://github.com/ryuya0124/gemini-microg-patches) "
        f"tag `{prov['upstream_tag']}`. These patches make **Gemini** work with "
        "**microG RE** (`app.revanced.android.gms` 7.0.0), including Samsung Secure "
        "Folder / work profile (user 150). They target the Google app and Gemini "
        "launcher — **not YouTube**.",
        "",
        "[![MicroG RE](https://img.shields.io/badge/MicroG%20RE-7.0.0-2e7d32)]"
        "(docs/gemini-microg-patches.md) "
        "[![Google App](https://img.shields.io/badge/Google-17.54.18.ve.arm64-4285F4)]"
        "(docs/gemini-microg-patches.md) "
        "[![Gemini](https://img.shields.io/badge/Gemini-1.0.958859967-6a5acd)]"
        "(docs/gemini-microg-patches.md)",
        "",
        "> ⚠️ **Reference source only** — this directory is outside the Gradle "
        "source sets, so it is **not compiled into `patch.mpp`**. To use these "
        "patches, add the upstream repo as a separate Manager source or import its "
        "`.mpp`. See [`docs/gemini-microg-patches.md`](docs/gemini-microg-patches.md) "
        "and the vendored [`README`](extras/gemini-microg-patches/README.md).",
        "",
        "| Target | Package | Version |",
        "| --- | --- | --- |",
        "| Google App (AGSA) | `com.google.android.googlequicksearchbox` | `17.54.18.ve.arm64` |",
        "| Gemini launcher | `com.google.android.apps.bard` | `1.0.958859967` |",
        "| microG RE | `app.revanced.android.gms` | `7.0.0` |",
        "",
        "បើកក្រុមខាងក្រោមដើម្បីមើល patches ទាំងអស់ / Expand a group to see every patch:",
        "",
    ]

    for group in order:
        members = buckets.get(group) or []
        if not members:
            continue
        lines += ["<details>", f"<summary>{group} • {len(members)}</summary>", ""]
        for item in sorted(members, key=lambda x: x["name"].lower()):
            suffix = "" if item["default"] else " — *disabled by default*"
            lines.append(f"- `{item['name']}`{suffix}")
        lines += ["", "</details>", ""]

    lines += [
        "> ចំណាំ៖ ស្លាក `gemini-*`, `google-*` និង `microg-re-*` ជា tags សម្រាប់សម្គាល់ "
        "កំណែដែលបានផ្ទៀងផ្ទាត់ (verified targets) — វាមិនបន្ថែម patch ថ្មីទេ។ "
        "Do not apply YouTube patches to Google/Gemini. Upstream requires its Gemini patches "
        "plus the official `Clone app` patch; follow that specific combination, not two overlapping full patch sets.",
        "",
        "</details>",
        END,
    ]
    block = "\n".join(lines).rstrip("\n")

    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit("README Gemini patch-list markers not found")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    README.write_text(pattern.sub(lambda _: block, text, count=1), encoding="utf-8")
    print(f"README Gemini catalog updated: {len(items)} patches, "
          f"{sum(1 for g in order if buckets.get(g))} groups")


if __name__ == "__main__":
    main()
