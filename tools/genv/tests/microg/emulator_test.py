#!/usr/bin/env python3
"""Offline runtime test: exact MPP guard, fake signer and published MicroG only.

Never installs or opens GenV, never uses accounts, and records no credentials.
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
    # A freshly booted old emulator can bring up its services slightly after
    # boot completion. Retry; if the service is absent entirely, the probe's
    # ConnectivityManager check below still has to report NETWORK:OFF.
    for mode, service in (('wifi', 'wifi'), ('data', 'phone')):
        failure = None
        for attempt in range(3):
            try:
                adb('shell', 'svc', mode, 'disable')
                failure = None
                break
            except RuntimeError as exc:
                failure = exc
                if attempt < 2: time.sleep(3)
        if failure is not None:
            status = adb('shell', 'service', 'check', service).lower()
            if 'not found' not in status and 'not declared' not in status:
                raise failure
            print(f'::notice::Emulator has no {service} service; checking actual connectivity', flush=True)


def read_screen() -> list[dict[str, str]]:
    adb('shell', 'uiautomator', 'dump', '/sdcard/guard-window.xml', timeout=45)
    return [n.attrib for n in ET.fromstring(adb('exec-out', 'cat', '/sdcard/guard-window.xml')).iter('node')]


def probe(expected: str) -> None:
    expected += ';NETWORK:OFF'
    adb('shell', 'am', 'force-stop', PROBE)
    adb('shell', 'am', 'start', '-n', PROBE + '/test.genv.microg.ProbeActivity')
    deadline = time.monotonic() + 100
    last = []
    while time.monotonic() < deadline:
        try:
            last = read_screen()
            for node in last:
                if node.get('text') == expected:
                    print('::notice::Offline synthetic probe: ' + expected, flush=True)
                    return
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
    api = adb('shell', 'getprop', 'ro.build.version.sdk').strip()
    result = {
        'status': 'passed', 'android_emulator_api': api,
        'guard_from_actual_mpp_extension_dex': True,
        'no_package_rejected': True, 'same_package_wrong_signer_rejected': True,
        'official_morphe_microg_7_3_0_universal_accepted': True,
        'official_signin_service_and_activity_selected': True,
        'disabled_official_package_rejected_then_enabled': True,
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
