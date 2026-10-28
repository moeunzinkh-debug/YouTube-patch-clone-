#!/usr/bin/env python3
"""Check the pinned upstream Gboard bundle, metadata and optional Morphe CLI listing."""

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "bundles/gboard"
EXPECTED_VERSION = "4.0.0"
EXPECTED_COUNT = 43
EXPECTED_PACKAGE = "com.google.android.inputmethod.latin"
EXPECTED_TARGET = "18.5.4.993608717-release-arm64-v8a"
EXPECTED_SHA256 = "fadf54bea20f337a03baddf2bd294c86d254a744456c6e53ee13f4ad25a58716"
EXPECTED_SIZE = 8_186_810
EXPECTED_COMMIT = "2eb71854accc7e906d3e4f5495b2a54ed1e2af47"
EXPECTED_TREE = "b8dc2c76f8a17259c2e3eaa6b9f8565fb19d730b"
EXPECTED_ASSET = "gboard-patches-4.0.0.mpp"
EXPECTED_URL = (
    "https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/"
    "download/Gboard-v4.0.0/" + EXPECTED_ASSET
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_metadata() -> tuple[dict, list[str]]:
    pin = json.loads((BUNDLE / "upstream.json").read_text(encoding="utf-8"))
    for key, expected in {
        "tag": "v4.0.0",
        "commit": EXPECTED_COMMIT,
        "git_tree": EXPECTED_TREE,
        "asset_sha256": EXPECTED_SHA256,
        "asset_size": EXPECTED_SIZE,
        "local_asset": EXPECTED_ASSET,
        "patches": EXPECTED_COUNT,
        "default_selected": EXPECTED_COUNT,
        "package": EXPECTED_PACKAGE,
        "supported_versions": [EXPECTED_TARGET],
    }.items():
        check(pin.get(key) == expected, f"Unexpected upstream pin: {key}")

    metadata_path = BUNDLE / "patches-list.json"
    upstream_path = ROOT / "extras/gboard-patches/patches-list.json"
    check(metadata_path.read_bytes() == upstream_path.read_bytes(), "Patch list differs from vendored upstream")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    check(metadata.get("version") == EXPECTED_VERSION, "Unexpected patch-list version")
    patches = metadata["patches"]
    check(len(patches) == EXPECTED_COUNT, "Unexpected number of patches")
    names = [patch["name"] for patch in patches]
    check(len(set(names)) == EXPECTED_COUNT, "Duplicate patch names")
    for patch in patches:
        check(patch.get("use") is True, f"Patch is not default selected: {patch['name']}")
        check(
            patch.get("compatiblePackages") == {EXPECTED_PACKAGE: [EXPECTED_TARGET]},
            f"Unexpected compatible package/version: {patch['name']}",
        )

    source = json.loads((BUNDLE / "patches-bundle.json").read_text(encoding="utf-8"))
    check(source.get("version") == EXPECTED_VERSION, "Manager source version mismatch")
    check(source.get("download_url") == EXPECTED_URL, "Manager source points to an unexpected bundle")
    check(source.get("page_url", "").endswith("/releases/tag/Gboard-v4.0.0"), "Manager source release link mismatch")
    # Morphe Manager's JsonPatchBundle uses kotlinx.datetime.LocalDateTime.
    check(datetime.fromisoformat(source["created_at"]).tzinfo is None, "Manager created_at must be a local date-time")
    checksum_file = (BUNDLE / f"{EXPECTED_ASSET}.sha256").read_text(encoding="ascii").strip()
    check(checksum_file == f"{EXPECTED_SHA256}  {EXPECTED_ASSET}", "Checksum file is incorrect")
    import update_catalog
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    check(readme.count(update_catalog.START) == 1 and readme.count(update_catalog.END) == 1, "Missing Gboard catalog markers")
    current = update_catalog.START + readme.split(update_catalog.START, 1)[1].split(update_catalog.END, 1)[0] + update_catalog.END
    check(current == update_catalog.render(), "Khmer Gboard catalog is out of date")
    return pin, names


def verify_asset(path: Path) -> dict:
    check(path.is_file(), f"Bundle does not exist: {path}")
    check(path.stat().st_size == EXPECTED_SIZE, "Bundle size differs from upstream")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    check(digest == EXPECTED_SHA256, "Bundle SHA-256 differs from upstream")
    check(zipfile.is_zipfile(path), "MPP is not a ZIP/JAR archive")
    with zipfile.ZipFile(path) as archive:
        check(archive.testzip() is None, "Corrupt ZIP entry in MPP")
        entries = archive.namelist()
        check("META-INF/MANIFEST.MF" in entries, "Missing bundle manifest")
        check(any(name.endswith(".class") for name in entries), "No compiled patch classes in MPP")
        manifest = archive.read("META-INF/MANIFEST.MF").decode("utf-8", errors="replace")
    return {"sha256": digest, "size": path.stat().st_size, "zip_entries": len(entries), "manifest": manifest}


def verify_cli_output(text: str, expected_names: list[str]) -> None:
    names = re.findall(r"^Name: (.+)$", text, flags=re.MULTILINE)
    enabled = re.findall(r"^Enabled: (.+)$", text, flags=re.MULTILINE)
    check(len(names) == EXPECTED_COUNT, f"Morphe listed {len(names)} patches instead of {EXPECTED_COUNT}")
    check(len(set(names)) == len(names) and set(names) == set(expected_names), "Morphe patch names do not match upstream")
    check(len(enabled) == EXPECTED_COUNT and all(value.lower() == "true" for value in enabled), "Morphe defaults differ")
    check(text.count("Package name: " + EXPECTED_PACKAGE) == EXPECTED_COUNT, "Morphe package metadata differs")
    check(text.count(EXPECTED_TARGET) == EXPECTED_COUNT, "Morphe target-version metadata differs")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-only", action="store_true", help="Do not require the binary")
    parser.add_argument("--verify-vendor", action="store_true", help="Also verify the tracked upstream Git tree")
    parser.add_argument("--mpp", type=Path, default=BUNDLE / EXPECTED_ASSET)
    parser.add_argument("--cli-output", type=Path, help="Output of Morphe Desktop list-patches")
    parser.add_argument("--write-report", type=Path, help="Write a truthful CI validation report")
    args = parser.parse_args()
    if args.write_report and (args.metadata_only or not args.cli_output or not args.verify_vendor):
        parser.error("A validation report requires the binary, CLI listing and vendor verification")
    _, names = load_metadata()
    if args.verify_vendor:
        import verify_vendor
        verify_vendor.main()
    asset = None if args.metadata_only else verify_asset(args.mpp)
    if args.cli_output:
        verify_cli_output(args.cli_output.read_text(encoding="utf-8"), names)
        print("Morphe Desktop listed exactly 43 default-selected Gboard patches and the expected target")
    if asset:
        print(f"Verified upstream release MPP: {asset['size']} bytes, SHA-256 {asset['sha256']}")
        print("Bundle manifest:\n" + asset["manifest"])
    print(f"Verified upstream metadata: {len(names)} patches, {EXPECTED_PACKAGE}, {EXPECTED_TARGET}")
    if args.write_report:
        run_id = os.environ.get("GITHUB_RUN_ID")
        repo = os.environ.get("GITHUB_REPOSITORY")
        report = {
            "upstream_tag": "v4.0.0",
            "upstream_commit": EXPECTED_COMMIT,
            "vendor_git_tree": EXPECTED_TREE,
            "bundle_sha256": asset["sha256"],
            "bundle_size": asset["size"],
            "morphe_desktop": "1.19.1",
            "morphe_desktop_sha256": "a51472252cd63b2eac635dbb5a154ff918bfc15268da89679feb3d760230c573",
            "checks": {
                "upstream_source_tree": "passed",
                "release_asset_sha256_and_zip": "passed",
                "catalog_matches_upstream": "passed",
                "desktop_patch_listing": "passed",
                "actual_gboard_apk_patch": "not tested",
                "android_device_runtime": "not tested",
                "khmer_language_features": "not tested",
            },
            "run_url": f"https://github.com/{repo}/actions/runs/{run_id}" if repo and run_id else None,
        }
        args.write_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {args.write_report}")


if __name__ == "__main__":
    main()
