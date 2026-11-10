#!/usr/bin/env python3
"""Check the disposable Manager 2.5.0 MicroG-only output; never launch GenV.

The optional single-module APKS input exercises Manager's merge path but does
not supply a real configuration/native split set. No APK is published.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from inspect_genv import ASSET_SHA256, check_asset
from verify_bundle import verify_bundle
from verify_microg_patched import (
    ANDROID, EXPECTED_METADATA, ROUTES, inspect_dex, manifest,
    verify_availability, verify_sign_in_intent, verify_manifest,
)
from verify_patched import read_methods


def verify(source: Path, output: Path, bundle: Path, mode: str, report: Path) -> None:
    if mode not in {'base', 'single-module-archive'}:
        raise ValueError('Unexpected diagnostic input mode')
    check_asset(source)
    bundle_info = verify_bundle(bundle)
    before, counts, old_availability, old_sign_in, old_guard = inspect_dex(source, original=True)
    after, _, new_availability, new_sign_in, guard = inspect_dex(output, original=False)
    if dict(counts) != ROUTES or old_guard or not guard:
        raise ValueError('Unexpected routing fingerprint or missing MicroG extension')
    if any(after.get(key) != values for key, values in before.items()):
        raise ValueError('Unreviewed DEX string changes')
    verify_availability(old_availability, new_availability)
    verify_sign_in_intent(old_sign_in, new_sign_in)
    if read_methods(source) != read_methods(output):
        raise ValueError('MicroG-only selection changed a reviewed PairIP or billing method')
    document = manifest(output)
    app = document.find('application')
    if app is None:
        raise ValueError('Application manifest missing')
    for key, value in EXPECTED_METADATA.items():
        matches = [node for node in app.findall('meta-data') if node.get(ANDROID + 'name') == key]
        if len(matches) != 1 or matches[0].get(ANDROID + 'value') != value:
            raise ValueError('Reviewed MicroG metadata absent or conflicting')
    if not any(x.get(ANDROID + 'name') == 'app.revanced.android.gms' for x in document.findall('./queries/package')):
        raise ValueError('MicroG package query missing')
    if mode == 'base':
        verify_manifest(manifest(source), document)
    check_asset(source)
    result = {
        'manager': '2.5.0', 'patcher': '2.3.0', 'android_emulator': 'API 29 x86_64',
        'bundle_version': bundle_info['version'], 'bundle_sha256': bundle_info['sha256'],
        'source_sha256': ASSET_SHA256, 'input_mode': mode,
        'input_note': ('Released GenV base only; required splits and native libraries absent' if mode == 'base'
                       else 'A synthetic archive containing ONLY the released base; Manager merge path exercised, but no real split modules included'),
        'selected_patches': ['Morphe MicroG Google sign-in support (experimental)'],
        'manager_saved_patched_output': 'passed',
        'microg_routes_guard_and_metadata': 'passed',
        'license_and_reviewed_billing_methods_unchanged': True,
        'real_full_split_merge_and_installed_genv_input': 'not tested',
        'huawei_real_genv_launch_and_live_login': 'not tested',
        'ci_run': f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
    }
    report.write_text(json.dumps(result, indent=2) + '\n')
    print('::notice::Manager 2.5.0 on API 29 patched the known base with only MicroG selected; no actual GenV runtime or login tested.')


if __name__ == '__main__':
    if len(sys.argv) != 6:
        raise SystemExit('usage: verify_manager25.py BASE OUTPUT BUNDLE MODE REPORT')
    verify(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], Path(sys.argv[5]))
