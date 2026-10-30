#!/usr/bin/env python3
"""Check a real Manager-saved APK without executing the app or using an account."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import zipfile
from pathlib import Path

from inspect_apk import verify_asset
from verify_bundle import NAME, SETTINGS_NAME, PACKAGE, VERSION_NAME, verify_bundle
from verify_patched import inspect, verify_methods, verify_settings


def libs(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as archive:
        return {name: hashlib.sha256(archive.read(name)).hexdigest()
                for name in archive.namelist() if name.startswith('lib/arm64-v8a/') and name.endswith('.so')}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base', type=Path)
    parser.add_argument('patched', type=Path)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    verify_asset(args.base)
    bundle = verify_bundle(args.bundle)
    before, after = inspect(args.base), inspect(args.patched)
    verify_methods(before, after)
    verify_settings(before, after, enabled=True)
    original_libs, output_libs = libs(args.base), libs(args.patched)
    if not original_libs or original_libs != output_libs:
        raise ValueError('Native arm64 libraries changed or are missing')
    result = {
        'manager': '2.3.0-dev.3', 'package': PACKAGE, 'version': VERSION_NAME, 'version_code': 50342,
        'input_sha256': 'f341a1b174bda7b5d1c95cb2fc84da238228a116844069ee962220acaf1e4e4c',
        'bundle_sha256': bundle['sha256'], 'selectors': [NAME, SETTINGS_NAME], 'selectors_default_enabled': False,
        'local_source_imported': True, 'experimental_app_versions_enabled': True,
        'both_patches_explicitly_selected': True, 'manager_patch_and_save': 'passed',
        'expected_dex_hooks': 'passed', 'original_integrity_check': 'preserved', 'native_arm64_libraries_unchanged': True,
        'original_publisher_signing_provenance': 'not established',
        'app_installed_or_launched_by_manager_test': False,
        'translation_runtime': 'not established by this Manager patch test',
        'ci_run': f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
    }
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print('Manager-saved APK contains both expected patches and preserves the integrity call and arm64 libraries')


if __name__ == '__main__':
    main()
