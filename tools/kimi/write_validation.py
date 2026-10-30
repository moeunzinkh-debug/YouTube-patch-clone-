#!/usr/bin/env python3
"""Write scoped evidence for the separately built Kimi bundle."""
import argparse
import hashlib
import json
import os
from pathlib import Path

from verify_bundle import verify_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mpp', required=True, type=Path)
    parser.add_argument('--dex-report', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    bundle = verify_bundle(args.mpp)
    dex = json.loads(args.dex_report.read_text())
    if dex.get('status') != 'passed_actual_mpp_patch_and_dex_inspection':
        raise ValueError('Real APK patch and DEX verification did not pass')
    output = {
        'bundle_version': bundle['version'], 'bundle_sha256': bundle['sha256'], 'bundle_bytes': bundle['bytes'],
        'ci_run': f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
        'input_apks_sha256': '7000c991b9e745ccd1d1ecffaff71c2295094cb4a7fce213d3ce1d3310050304',
        'input_base_sha256': dex['input_base_sha256'],
        'input_signer_sha256': 'a40da80a59d170caa950cf15c18c454d47a39b26989d8b640ecd745ba71bf5dc',
        'input_trust': 'User-supplied APKS was signed with a public Android test key; not verified as an unmodified Moonshot APK.',
        'package': 'com.moonshot.kimichat', 'version': '3.1.5', 'version_code': 381,
        'patch': 'Remove license check', 'patch_default': True,
        'tests': {
            'build_and_metadata': 'passed', 'morphe_desktop_listing': 'passed',
            'morphe_desktop_patch_base_apk': 'passed', 'two_pairip_dex_early_returns': 'passed',
            'other_checked_methods_unchanged': 'passed',
            'manager_apks_merge_and_patch': 'not tested by this Desktop CI run; see manager-smoke.json for any later Manager test', 'android_runtime': 'not tested',
            'live_login_server_attestation_and_paid_features': 'not tested',
        },
        'scope': 'Disables reviewed local PairIP license entry points; no server entitlement or integrity verdict is changed.',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + '\n')
    print('Wrote Kimi build and verification report:', hashlib.sha256(args.mpp.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
