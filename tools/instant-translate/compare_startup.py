#!/usr/bin/env python3
"""Summarize three disposable emulator startup probes without leaking log text."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from verify_bundle import verify_bundle

INTEGRITY_FRAME = 'bin.edisaputra.protector.LicenseActivity.verifyIntegrity'


def outcome(report: dict) -> dict:
    return {
        'installed': 'Success' in (report.get('install') or '').splitlines(),
        'main_activity_reached': bool(report.get('main_activity_reached')),
        'app_ui_visible': bool(report.get('app_ui_visible')),
        'process_alive_not_proof_of_launch': bool(report.get('process_alive')),
        'app_fatal_exception': bool(report.get('app_fatal_exception')),
        'crash_dialog_seen': bool(report.get('crash_dialog_seen')),
        'exception_types': report.get('exception_types', []),
        'integrity_in_stack': INTEGRITY_FRAME in report.get('stack_frames', []),
        'exception_message_keywords': report.get('exception_message_keywords', []),
    }


def compare(original: dict, control: dict, manager: dict) -> tuple[dict, str]:
    cases = {'original': outcome(original), 'resigned_control': outcome(control), 'manager_patched': outcome(manager)}
    if not all(item['installed'] for item in cases.values()):
        return cases, 'inconclusive_install_failed'
    baseline = cases['original']
    if not baseline['main_activity_reached'] or baseline['app_fatal_exception'] or baseline['crash_dialog_seen']:
        return cases, 'inconclusive_original_baseline'
    c, m = cases['resigned_control'], cases['manager_patched']
    if c['app_fatal_exception'] and c['integrity_in_stack'] and m['app_fatal_exception'] and m['integrity_in_stack']:
        return cases, 'same_integrity_stack_in_manager_and_unchanged_dex_resign_control'
    return cases, 'different_or_inconclusive_outcomes'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('control', type=Path)
    parser.add_argument('manager', type=Path)
    parser.add_argument('manager_validation', type=Path)
    parser.add_argument('signatures', type=Path)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    reports = [json.loads(path.read_text()) for path in (args.original, args.control, args.manager)]
    if [r.get('mode') for r in reports] != ['original', 'resigned_control', 'manager_patched']:
        raise ValueError('Unexpected startup report modes')
    environments = {(r.get('abi_list'), r.get('native_bridge'), r.get('wifi_on')) for r in reports}
    if len(environments) != 1:
        raise ValueError('Startup comparisons used different emulator conditions')
    bundle = verify_bundle(args.bundle)
    manager_validation = json.loads(args.manager_validation.read_text())
    if manager_validation.get('bundle_sha256') != bundle['sha256'] or manager_validation.get('manager_patch_and_save') != 'passed':
        raise ValueError('Manager output was not validated against this bundle')
    signatures = json.loads(args.signatures.read_text())
    if signatures.get('original_signer_sha256') != 'a3f608b5c58f687d8768c378fea8e2f06426715a36194656beaddd39400ede8d':
        raise ValueError('Original signer differs from the inspected APK')
    cases, conclusion = compare(*reports)
    abi_list, native_bridge, wifi_on = environments.pop()
    result = {
        'scope': 'Disposable Android 15 x86_64 emulator with ARM64 native bridge; startup only',
        'package': 'com.spaceship.screen.textcopy', 'version': 'v7.5.00300',
        'input_sha256': 'f341a1b174bda7b5d1c95cb2fc84da238228a116844069ee962220acaf1e4e4c',
        'bundle_sha256': bundle['sha256'], 'abi_list': abi_list, 'native_bridge': native_bridge,
        'wifi_on': wifi_on, 'control_dex_and_native_libraries': 'byte-identical to original',
        'signatures': signatures,
        'manager_output': 'both patches selected, signed and statically verified',
        'cases': cases, 'conclusion': conclusion,
        'actual_cause': 'not established; re-signing and zip alignment both change APK packaging',
        'integrity_check': 'preserved; no bypass used',
        'real_arm64_devices_or_users_apk': 'not tested',
        'ci_run': f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
    }
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Startup comparison:', conclusion)


if __name__ == '__main__':
    main()
