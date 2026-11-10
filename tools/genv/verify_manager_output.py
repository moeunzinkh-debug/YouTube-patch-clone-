#!/usr/bin/env python3
"""Inspect Manager's disposable saved GenV base APK without installing it."""
from __future__ import annotations
import argparse
import json
import os
import zipfile
from pathlib import Path
from inspect_genv import ASSET_SHA256, check_asset
from verify_bundle import verify_bundle
from verify_patched import read_methods, verify_methods
from verify_microg_patched import verify_contents


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base', type=Path)
    parser.add_argument('patched', type=Path)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    check_asset(args.base)
    bundle = verify_bundle(args.bundle)
    verify_methods(read_methods(args.base), read_methods(args.patched))
    microg = verify_contents(args.base, [args.patched])
    with zipfile.ZipFile(args.base) as source, zipfile.ZipFile(args.patched) as output:
        native = [name for name in output.namelist() if name.startswith('lib/') and name.endswith('.so')]
        if native: raise ValueError('Expected an incomplete base APK without native split libraries')
        manifest_same = source.read('AndroidManifest.xml') == output.read('AndroidManifest.xml')
    check_asset(args.base)
    result = {
        'manager': '2.3.0-dev.3', 'android_emulator': 'API 35 x86_64',
        'input': 'GenV release base APK only; required configuration and native splits unavailable',
        'input_sha256': ASSET_SHA256,
        'package': 'com.ainate.ai.video.generate', 'version': '3.7.2', 'version_code': 163,
        'bundle_version': bundle['version'], 'bundle_sha256': bundle['sha256'],
        'imported_local_source': True, 'experimental_app_versions_enabled': True,
        'selected_patches': ['Remove license check', 'Morphe MicroG Google sign-in support (experimental)'],
        'manager_patch_incomplete_base': 'passed',
        'saved_output_pairip_early_returns_and_selected_controls': 'passed',
        'saved_output_microg_routing_and_manifest': microg['status'],
        'saved_output_manifest_byte_identical': manifest_same,
        'saved_output_contains_native_libraries': False,
        'full_split_merge_or_complete_app': 'not tested',
        'app_installed_or_launched': False,
        'live_login_server_attestation_and_paid_features': 'not tested',
        'ci_run': f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print('Manager saved an incomplete base with PairIP and reviewed MicroG changes; runtime not tested')

if __name__ == '__main__': main()
