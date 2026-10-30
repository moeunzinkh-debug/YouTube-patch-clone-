#!/usr/bin/env python3
"""Verify Manager's saved merged APK without installing or launching Kimi."""
import argparse
import hashlib
import json
import os
import zipfile
from pathlib import Path

from inspect_apks import digest_file
from verify_bundle import verify_bundle
from verify_patched import BASE_SHA256, read_methods, verify_methods


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base', type=Path)
    parser.add_argument('patched', type=Path)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    if digest_file(args.base) != BASE_SHA256:
        raise ValueError('Incorrect original Kimi base APK')
    bundle = verify_bundle(args.bundle)
    verify_methods(read_methods(args.base), read_methods(args.patched))
    with zipfile.ZipFile(args.patched) as apk:
        native_arm64 = [name for name in apk.namelist() if name.startswith('lib/arm64-v8a/') and name.endswith('.so')]
        if not native_arm64:
            raise ValueError('Merged APK does not contain the original arm64 split libraries')
    report = {
        'manager': '2.3.0-dev.3', 'patcher': '2.1.0-dev.1', 'android_emulator': 'API 35 x86_64',
        'input': 'user-supplied Kimi split APKS, SHA-256 7000c991b9e745ccd1d1ecffaff71c2295094cb4a7fce213d3ce1d3310050304',
        'input_trust': 'already re-signed with the public Android test key; original publisher authenticity not verified',
        'package': 'com.moonshot.kimichat', 'version': '3.1.5', 'version_code': 381,
        'bundle_version': bundle['version'], 'bundle_sha256': bundle['sha256'],
        'imported_local_source': True, 'experimental_app_versions_enabled': True,
        'selected_patch': 'Remove license check', 'manager_patch_and_split_merge': 'passed',
        'saved_output_pairip_early_returns_and_other_checked_methods': 'passed',
        'saved_output_contains_arm64_libraries': True, 'arm64_libraries_count': len(native_arm64),
        'patched_apk_sha256_for_test': hashlib.sha256(args.patched.read_bytes()).hexdigest(),
        'app_installed_or_launched': False, 'live_login_server_attestation_and_paid_features': 'not tested',
        'ci_run': f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print('Manager output contains the expected PairIP edits and merged arm64 libraries')


if __name__ == '__main__':
    main()
