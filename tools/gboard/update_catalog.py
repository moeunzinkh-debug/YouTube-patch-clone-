#!/usr/bin/env python3
"""Render the Khmer Gboard catalog from upstream metadata and translations."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
START = "<!-- GBOARD-PATCH-LIST:START -->"
END = "<!-- GBOARD-PATCH-LIST:END -->"


def render() -> str:
    upstream = json.loads((ROOT / "bundles/gboard/patches-list.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "tools/gboard/catalog.json").read_text(encoding="utf-8"))
    if catalog["version"] != upstream["version"]:
        raise ValueError("Catalog version differs from upstream patch metadata")
    expected = [patch["name"] for patch in upstream["patches"]]
    actual = [patch["name"] for group in catalog["groups"] for patch in group["patches"]]
    if len(expected) != len(set(expected)) or len(actual) != len(set(actual)):
        raise ValueError("Duplicate patch names")
    if set(expected) != set(actual):
        raise ValueError(f"Catalog mismatch: missing={set(expected) - set(actual)}, extra={set(actual) - set(expected)}")
    lines = [
        START,
        '<a id="gboard-patches"></a>',
        "<details>",
        f"<summary>⌨️ Gboard • {len(actual)} patches (bundle ដាច់ដោយឡែក)</summary>",
        "",
        "ប្រភព៖ [jasonwu1994/Gboard-patches v4.0.0](https://github.com/jasonwu1994/Gboard-patches/releases/tag/v4.0.0)។",
        "Bundle នេះគឺជាច្បាប់ចម្លងឯកសារ `.mpp` របស់ upstream ដោយមិនកែប្រែ; វា **មិនមែន** `patch.mpp` របស់ YouTube ទេ។",
        "",
        "គោលដៅដែល upstream រាយ៖ `com.google.android.inputmethod.latin` កំណែ",
        "`18.5.4.993608717-release-arm64-v8a` ប៉ុណ្ណោះ។ Patches ទាំង 43 ត្រូវបានជ្រើសជាមុនក្នុង upstream;",
        "នេះមិនមានន័យថាមុខងារបណ្ដាញទាំងអស់ចាប់ផ្ដើមដោយស្វ័យប្រវត្តិទេ។ ពិនិត្យជម្រើសមុន patch។",
        "",
        "[ទាញយក Gboard bundle](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/Gboard-v4.0.0) ·",
        "[ការដំឡើង សុវត្ថិភាព និងកម្រិតកំណត់](bundles/gboard/README.md) ·",
        "[Source និងអាជ្ញាបណ្ណ](extras/gboard-patches/)",
        "",
    ]
    for group in catalog["groups"]:
        lines.extend([
            "<details>",
            f'<summary>{group["title"]} • {len(group["patches"])}</summary>',
            "",
        ])
        lines.extend(f'- `{patch["name"]}` — {patch["khmer"]}' for patch in group["patches"])
        lines.extend(["", "</details>", ""])
    lines.extend([
        "**សុវត្ថិភាព៖** FTP, Web Clipboard, JavaScript និង signature bypass មានផលប៉ះពាល់លើសុវត្ថិភាព/ទិន្នន័យ;",
        "ដកជម្រើសដែលមិនត្រូវការ និងប្រើតែនៅក្នុងបណ្ដាញដែលទុកចិត្ត។ រក្សាក្តារចុចមួយផ្សេងទៀតទុកជាបម្រុង។",
        "OCR មិនរាយភាសាខ្មែរ ហើយមុខងារភាសាខ្មែរមិនត្រូវបានផ្ទៀងផ្ទាត់នៅទីនេះទេ។",
        "",
        "</details>",
        END,
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail instead of updating an out-of-date catalog")
    args = parser.parse_args()
    path = ROOT / "README.md"
    content = path.read_text(encoding="utf-8")
    if content.count(START) != 1 or content.count(END) != 1:
        raise ValueError("README must contain exactly one Gboard catalog marker pair")
    before, rest = content.split(START, 1)
    _, after = rest.split(END, 1)
    updated = before + render() + after
    if args.check:
        if updated != content:
            raise SystemExit("Gboard catalog is out of date; run tools/gboard/update_catalog.py")
        print("Gboard README catalog matches all upstream patch names")
    else:
        path.write_text(updated, encoding="utf-8")
        print("Updated Gboard README catalog")


if __name__ == "__main__":
    main()
