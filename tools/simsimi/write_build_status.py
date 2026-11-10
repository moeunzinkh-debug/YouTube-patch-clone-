#!/usr/bin/env python3
"""Update the SimSimi build status only after every CI build/application check passes."""
import hashlib
import json
import os
from pathlib import Path

folder = Path('bundles/simsimi')
status_path = folder / 'build-status.json'
status = json.loads(status_path.read_text())
status.pop('target_version', None)
status.pop('target_version_code', None)
quick = json.loads((folder / 'quick-validation.json').read_text())
for key in ('quick_return_with_pull_reload', 'quick_return_without_pull_reload', 'pull_reload_without_quick_return'):
    if quick[key] != 'passed_static_apk_inspection':
        raise SystemExit(f'Missing Quick Return matrix result: {key}')
bundle = (folder / 'bundle.mpp').read_bytes()
name = 'Quick return: double-tap Chat (experimental)'
patches = status['implemented_patches']
if name not in patches:
    patches.append(name)
status.update({
    'version': '0.5.0-dev.1',
    'target_versions': ['9.2.3', '9.2.6'],
    'target_version_codes': {'9.2.3': '1119001', '9.2.6': '1125001'},
    'compatibility_note': '9.2.6 has a separately reviewed Hermes/native profile and is applied by CI to the exact uploaded APK. Daily bonus remains 9.2.3-only because its 9.2.6 flow changed.',
    'input_constraint': 'CI input is the exact uploaded SimSimi 9.2.6 APK (SHA-256 756ffb436399d6f74b2f05b234b89a9d7b15ba40bbbcb3c7b6ff2913a288556e). Device installation/runtime is not tested.',
    'ci_run': f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
    'bundle_sha256': hashlib.sha256(bundle).hexdigest(),
    'bundle_bytes': len(bundle),
    'quick_return_scope': 'Opt-in. Double-tapping the selected second bottom Chat tab on the English Conversation screen scrolls the largest visible vertical ScrollView to y=0. It does not reload. Layout and device behavior remain unverified.',
    'pull_reload_scope': 'English Conversation list only. Requires a real ACTION_MOVE and two stable delayed Conversation checks before React reload; opening a chat must not reload. Device behavior remains unverified.',
})
status['tests'].update({
    'morphe_selector_names_defaults_and_compatibility': 'passed_12_selectors_for_9.2.3_and_11_for_9.2.6_daily_bonus_923_only',
    'simsimi_9.2.6_actual_apk_application': 'passed_combined_quick_only_pull_only_static_output',
    'pull_gesture_java_harness': 'passed_15_checks_including_navigation_transition_rejection',
    'pull_reload_apk_guard_sequence': 'passed_move_and_two_delayed_stability_checks',
    'quick_return_double_tap_host_harness': 'passed_20_checks',
    'quick_return_android_stubs_host_harness': 'passed_15_checks_not_android_runtime',
    'quick_return_apk_comparator_unit_tests': 'passed_7_tests_on_synthetic_methods',
    'quick_return_morphe_application_matrix': 'passed_combined_quick_only_pull_only_static_output',
    'quick_return_device_runtime': 'not_run',
})
pending = 'quick_return_bottom_tab_and_scroll_on_device'
if pending not in status['pending_features']:
    status['pending_features'].append(pending)
status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + '\n')
print('Wrote source status for', len(bundle), 'byte experimental bundle')
