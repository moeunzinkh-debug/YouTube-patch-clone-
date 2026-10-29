#!/usr/bin/env python3
"""Write truthful build and optional real-APK test status after CI verification."""
import hashlib
import json
import os
import sys
from pathlib import Path

from verify_bundle import VERSION, COMMIT, metadata, verify_archive

folder = Path('bundles/telegram')
bundle = folder / 'bundle.mpp'
source = metadata()
archive = verify_archive(bundle)
if hashlib.sha256(bundle.read_bytes()).hexdigest() != archive['sha256']:
    raise SystemExit('Bundle changed after verification')
smoke = json.loads(Path(sys.argv[1]).read_text())
if smoke.get('status') not in {'passed_actual_mpp_on_telegram_signed_apk', 'not_tested_apk_download_unavailable'}:
    raise SystemExit('Unexpected actual-APK test status')
repo = os.environ['GITHUB_REPOSITORY']
run = os.environ['GITHUB_RUN_ID']
report = {
    'fork_version': VERSION,
    'upstream_tag': source['upstream_tag'],
    'upstream_commit': COMMIT,
    'bundle_sha256': archive['sha256'],
    'bundle_bytes': archive['bytes'],
    'ci_run': f'https://github.com/{repo}/actions/runs/{run}',
    'tests': {
        'upstream_source_blob_verification': 'passed',
        'isolated_mpp_compile': 'passed',
        'mpp_zip_checksum_and_telegram_only_classes': 'passed',
        'morphe_desktop_1_19_1_listing_and_targets': 'passed_15_selectors',
        'actual_apk_application': smoke,
        'android_manager_ui': 'not_tested',
        'android_emulator_launch': 'See android-smoke.json when its bundle SHA-256 matches; launch smoke only.',
        'physical_device_runtime_login_notifications': 'not_tested',
        'server_side_premium_or_download_speed': 'not_verified',
    },
    'upstream_patch_defaults': 'All 15 selectable patches default on; Disable analytics targets Telegram Plus only.',
    'scope': 'Telegram, Telegram Web and Telegram Plus only; generic helpers are anonymous dependencies.',
    'release_published': False,
}
(folder / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
print('Wrote Telegram build report:', smoke['status'])
