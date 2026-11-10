#!/usr/bin/env python3
"""Offline test of the MPP guard and a synthetic MicroG sign-in handoff.

Never installs or opens GenV, never uses accounts, and records no credentials.
The synthetic test deliberately stops at MicroG's empty-account UI: it does
not authenticate or prove the real GenV app's behavior.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

PROBE = 'test.genv.microg'
MICROG = 'app.revanced.android.gms'


def adb(*args: str, timeout: int = 90) -> str:
    result = subprocess.run(['adb', *args], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"adb {' '.join(args[:4])}: {(result.stdout + result.stderr)[-400:]}")
    return result.stdout


def disable_network() -> None:
    # Some API 24 emulator images return an error from svc wifi even when no
    # usable Wi-Fi radio exists. Airplane mode and both svc commands are best
    # effort; each probe independently checks ConnectivityManager is offline.
    adb('shell', 'settings', 'put', 'global', 'airplane_mode_on', '1')
    for command in (
        ('shell', 'am', 'broadcast', '-a', 'android.intent.action.AIRPLANE_MODE', '--ez', 'state', 'true'),
        ('shell', 'svc', 'wifi', 'disable'),
        ('shell', 'svc', 'data', 'disable'),
    ):
        try:
            adb(*command)
        except RuntimeError:
            # Offline state is verified by the synthetic app, not assumed from
            # a shell command's return code. No account is present regardless.
            pass


def read_screen() -> list[dict[str, str]]:
    adb('shell', 'uiautomator', 'dump', '/sdcard/guard-window.xml', timeout=45)
    return [n.attrib for n in ET.fromstring(adb('exec-out', 'cat', '/sdcard/guard-window.xml')).iter('node')]


def probe(expected: str) -> None:
    guarded = expected.startswith('GUARD:YES;')
    expected += ';PREPARE:' + ('YES' if guarded else 'NO')
    expected += ';MODE:' + ('4' if guarded else '2') + ';NETWORK:OFF'
    disable_network()
    adb('shell', 'am', 'force-stop', PROBE)
    adb('shell', 'am', 'start', '-n', PROBE + '/test.genv.microg.ProbeActivity')
    deadline = time.monotonic() + 100
    last_retry = time.monotonic()
    last = []
    while time.monotonic() < deadline:
        try:
            last = read_screen()
            for node in last:
                if node.get('text') == expected:
                    print('::notice::Offline synthetic probe: ' + expected, flush=True)
                    return
            # A first-boot setup component can re-enable a network after the
            # previous probe. Reapply airplane mode and refresh this screen.
            if any(node.get('text', '').startswith('GUARD:') and node.get('text', '').endswith(';NETWORK:ON') for node in last) and time.monotonic() - last_retry > 10:
                disable_network()
                adb('shell', 'am', 'force-stop', PROBE)
                adb('shell', 'am', 'start', '-n', PROBE + '/test.genv.microg.ProbeActivity')
                last_retry = time.monotonic()
            # Avoid transient first-boot Google setup ANR dialogs covering the probe.
            if any("isn't responding" in node.get('text', '') for node in last):
                for node in last:
                    if node.get('text') in ('Wait', 'Close app'):
                        p = re.findall(r'\d+', node.get('bounds', ''))
                        if len(p) == 4:
                            x1, y1, x2, y2 = map(int, p)
                            adb('shell', 'input', 'tap', str((x1 + x2) // 2), str((y1 + y2) // 2))
                            break
            time.sleep(2)
        except (RuntimeError, ET.ParseError):
            time.sleep(2)
    # The fixture's only displayed data are fixed GUARD/SERVICE/ACTIVITY labels.
    fixed = [n.get('text', '') for n in last if n.get('text', '').startswith('GUARD:')]
    raise RuntimeError(f'Expected {expected}; observed {fixed[:2]}')


def wait_handoff_result(expected: str) -> None:
    deadline = time.monotonic() + 100
    last = []
    while time.monotonic() < deadline:
        try:
            last = read_screen()
            if any(node.get('text') == expected for node in last):
                print('::notice::Offline synthetic handoff: ' + expected, flush=True)
                return
            time.sleep(2)
        except (RuntimeError, ET.ParseError):
            time.sleep(2)
    fixed = [n.get('text', '') for n in last if n.get('text', '').startswith('HANDOFF:')]
    raise RuntimeError(f'Expected fixed handoff result; observed {fixed[:2]}')


def start_handoff(mismatch: bool) -> None:
    disable_network()
    adb('shell', 'am', 'force-stop', PROBE)
    adb('shell', 'am', 'start', '-n', PROBE + '/test.genv.microg.HandoffProbeActivity',
        '--ez', 'mismatch', 'true' if mismatch else 'false')


def has_microg_account(account_dump: str) -> bool:
    return bool(re.search(r'Account\s*\{[^}]*\btype\s*=\s*app\.revanced(?:\s|,|\})', account_dump))


def assert_no_microg_account() -> None:
    # The emulator is disposable. Never print the account-manager dump; abort
    # instead if an actual account of MicroG's type is unexpectedly present.
    if has_microg_account(adb('shell', 'dumpsys', 'account')):
        raise RuntimeError('MicroG account unexpectedly present in synthetic emulator')


def wait_empty_account_screen() -> None:
    target = MICROG + '/org.microg.gms.auth.login.LoginActivity'
    deadline = time.monotonic() + 100
    while time.monotonic() < deadline:
        # Only compare fixed package/activity identifiers in memory. Do not
        # record the activity dump or any UI contents from the sign-in screen.
        activities = adb('shell', 'dumpsys', 'activity', 'activities')
        resumed = [line for line in activities.splitlines() if any(
            marker in line for marker in ('mResumedActivity', 'topResumedActivity', 'mFocusedActivity', 'Resumed:'))]
        if any(target in line for line in resumed):
            print('::notice::Synthetic caller reached MicroG empty-account activity offline.', flush=True)
            return
        time.sleep(2)
    raise RuntimeError('Synthetic caller did not reach the expected MicroG empty-account activity')


def main() -> None:
    work, bundle, official, report = map(Path, sys.argv[1:5])
    disable_network()
    adb('install', '-r', str(work / 'probe.apk'), timeout=180)
    probe('GUARD:NO;SERVICE:NONE;ACTIVITY:NONE')

    adb('install', '-r', str(work / 'fake.apk'), timeout=180)
    probe('GUARD:NO;SERVICE:AUTH;ACTIVITY:AUTH')
    adb('uninstall', MICROG, timeout=180)
    probe('GUARD:NO;SERVICE:NONE;ACTIVITY:NONE')

    adb('install', '-r', str(official), timeout=300)
    probe('GUARD:YES;SERVICE:AUTH;ACTIVITY:AUTH')
    adb('shell', 'pm', 'disable-user', '--user', '0', MICROG)
    probe('GUARD:NO;SERVICE:NONE;ACTIVITY:NONE')
    adb('shell', 'pm', 'enable', MICROG)
    probe('GUARD:YES;SERVICE:AUTH;ACTIVITY:AUTH')

    # No real account or credential is present. A mismatching caller must be
    # rejected; the correct synthetic caller should reach MicroG's add-account
    # activity, without filling it or proceeding to a real authentication.
    assert_no_microg_account()
    start_handoff(mismatch=True)
    wait_handoff_result('HANDOFF:MISMATCH_REJECTED;NETWORK:OFF')
    start_handoff(mismatch=False)
    wait_empty_account_screen()
    adb('shell', 'am', 'force-stop', MICROG)
    adb('shell', 'am', 'force-stop', PROBE)
    assert_no_microg_account()

    api = adb('shell', 'getprop', 'ro.build.version.sdk').strip()
    result = {
        'status': 'passed', 'android_emulator_api': api,
        'guard_from_actual_mpp_extension_dex': True,
        'no_package_rejected': True, 'same_package_wrong_signer_rejected': True,
        'official_morphe_microg_7_3_0_universal_accepted': True,
        'official_signin_service_and_activity_selected': True,
        'disabled_official_package_rejected_then_enabled': True,
        'synthetic_stale_mode_refreshed_only_with_actual_guard_acceptance': True,
        'synthetic_mode_note': 'synthetic fixture mirrors the injected decision; it is not GenV code',
        'synthetic_mismatched_caller_rejected': True,
        'synthetic_caller_reached_microg_empty_account_activity': True,
        'synthetic_handoff_scope': 'null-options test parcel, no account, no authentication; not the GenV app or its code',
        'bundle_sha256': hashlib.sha256(bundle.read_bytes()).hexdigest(),
        'official_microg_apk_sha256': hashlib.sha256(official.read_bytes()).hexdigest(),
        'network_disabled': True, 'accounts_used': False, 'real_genv_installed_or_launched': False,
        'oauth_server_acceptance_and_user_device': 'not tested',
        'ci_run': f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('::error title=Offline MicroG guard test::' + str(exc)[:1000], flush=True)
        sys.exit(1)
