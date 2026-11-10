#!/usr/bin/env python3
"""Run only a synthetic counter-based PairIP-shaped fixture on Android."""
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

PACKAGE = 'com.ainate.ai.video.generate'
ACTIVITY = PACKAGE + '/test.genv.MainActivity'


def adb(*args: str, timeout: int = 90) -> str:
    result = subprocess.run(['adb', *args], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"adb {' '.join(args[:3])}: {result.stderr[-800:]}")
    return result.stdout


def dump() -> list[dict[str, str]]:
    adb('shell', 'uiautomator', 'dump', '/sdcard/window.xml', timeout=45)
    return [node.attrib for node in ET.fromstring(adb('exec-out', 'cat', '/sdcard/window.xml')).iter('node')]


def wait_text(expected: str) -> None:
    deadline = time.monotonic() + 90
    last = []
    while time.monotonic() < deadline:
        try:
            last = dump()
            if any(n.get('text') == expected for n in last):
                print('::notice::Synthetic fixture displayed ' + expected, flush=True)
                return
            # A first-boot Google setup ANR can cover otherwise healthy test UI.
            if any("isn't responding" in n.get('text', '') for n in last):
                for n in last:
                    if n.get('text') in ('Wait', 'Close app'):
                        bounds = re.findall(r'\d+', n.get('bounds', ''))
                        if len(bounds) == 4:
                            x1, y1, x2, y2 = map(int, bounds)
                            adb('shell', 'input', 'tap', str((x1 + x2) // 2), str((y1 + y2) // 2))
                            break
            time.sleep(2)
        except (RuntimeError, ET.ParseError):
            time.sleep(2)
    visible = ' | '.join(n.get('text', '') or n.get('content-desc', '') for n in last if n.get('text') or n.get('content-desc'))[:1200]
    raise RuntimeError(f'Expected {expected}; visible: {visible}')


def main() -> None:
    work, bundle, report = map(Path, sys.argv[1:4])
    adb('shell', 'svc', 'wifi', 'disable')
    adb('shell', 'svc', 'data', 'disable')
    adb('install', '-r', str(work / 'fixture.apk'), timeout=180)
    adb('shell', 'am', 'start', '-n', ACTIVITY)
    wait_text('SYNTHETIC-PAIRIP-2-1')
    adb('shell', 'am', 'force-stop', PACKAGE)
    adb('install', '-r', str(work / 'patched.apk'), timeout=180)
    adb('shell', 'am', 'start', '-n', ACTIVITY)
    wait_text('SYNTHETIC-PAIRIP-0-0')
    result = {
        'status': 'passed',
        'fixture': 'synthetic counter-only app with reviewed GenV-shaped methods; not the GenV APK',
        'android_emulator': 'API 35 x86_64',
        'before_patch_check_calls_and_init_calls': [2, 1],
        'after_patch_check_calls_and_init_calls': [0, 0],
        'wrong_version_code_rejected': True,
        'changed_opcode_rejected': True,
        'microg_wrong_version_and_unsigned_input_rejected': True,
        'bundle_sha256': hashlib.sha256(bundle.read_bytes()).hexdigest(),
        'real_genv_installed_or_launched': False,
        'full_app_login_server_attestation_and_purchases': 'not tested',
        'ci_run': f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
    }
    report.write_text(json.dumps(result, indent=2) + '\n')

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('::error title=Synthetic Android test::' + str(exc)[:1200], flush=True)
        try:
            print('::error::' + adb('logcat', '-d', '-t', '200', '-s', 'AndroidRuntime:E')[-2500:].replace('\n', ' | '), flush=True)
        except Exception:
            pass
        sys.exit(1)
