#!/usr/bin/env python3
"""Write a limited, honest report only after the configured CI checks pass."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

if len(sys.argv) != 5:
    raise SystemExit('usage: write_validation.py bundle.mpp dex-report.json android-report.json output.json')
bundle, dex_report, android_report, output = map(Path, sys.argv[1:])
dex = json.loads(dex_report.read_text())
android = json.loads(android_report.read_text())
if dex.get('server_response_and_add_email_hooks') != 'passed_single_and_default_plus_experiment':
    raise ValueError('The real patched-APK hooks were not verified')
if android.get('outcome') != 'passed' or android.get('synthetic_add_email_ui') != 'passed_no_offer_and_server_offered_timeout':
    raise ValueError('The synthetic Android test did not pass')
digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
report = {
    'fork_version': '1.23.1-tg.email-exp.1',
    'upstream': 'rushiranpise/morphe-patches v1.23.1, commit 92c0fca0ae103a419c7fc61f9c5b8b38b7d6b82a',
    'experiment_selector': 'Try another login method (experimental)',
    'experiment_default': False,
    'bundle_sha256': digest,
    'bundle_bytes': bundle.stat().st_size,
    'ci_run': f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
    'checks': {
        'upstream_blob_and_original_telegram_sources': 'passed',
        'synthetic_jvm_bridge_tests': 'passed; synthetic data and stubs only',
        'morphe_desktop_1_19_1_catalog': 'passed; 15 upstream selectors and one default-off experiment',
        'real_telegram_web_12_10_1_apk_patching': 'passed; experiment only and 14 defaults plus experiment',
        'real_apk_dex_hooks_and_reflection_fields': dex,
        'android_emulator_synthetic_ui': android,
        'google_play_apk_and_physical_device': 'not_tested',
        'real_telegram_login_next_type_and_resend': 'not_tested',
        'free_otp_or_sms_fee_bypass': 'not_verified_and_not_guaranteed',
        'morphe_manager_android_ui': 'not_tested',
    },
    'scope': 'Offer one manual alternative only for a server-supplied SMS/call next_type; otherwise retain Add Email.',
    'release_published': False,
}
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'bundle_sha256': digest, 'bytes': bundle.stat().st_size, 'ci_run': report['ci_run']}))
