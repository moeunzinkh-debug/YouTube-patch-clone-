#!/usr/bin/env python3
"""Inspect Settings of the original APK in a disposable emulator, without private data."""
import json
import os
import re
import subprocess
import time
from pathlib import Path

from probe_runtime import ACTIVITY, PACKAGE, adb, dump, maybe_click, safe_label, snapshot

DIR = Path(os.environ['RUNNER_TEMP']) / 'instant-settings'
INPUT = DIR / 'input.apk'
OUTPUT = DIR / 'settings-runtime.json'


def screenshot(name):
    result = subprocess.run(['adb', 'exec-out', 'screencap', '-p'], capture_output=True, timeout=30, check=True)
    (DIR / f'{name}.png').write_bytes(result.stdout)


def click_label(nodes, text, lower_y=0):
    for node in nodes:
        label = safe_label(node.get('text') or node.get('content-desc') or '')
        bounds = node.get('bounds', '')
        if label.casefold() != text.casefold() or not re.fullmatch(r'\[\d+,\d+\]\[\d+,\d+\]', bounds):
            continue
        a, b, c, d = map(int, re.findall(r'\d+', bounds))
        if b < lower_y:
            continue
        adb('shell', 'input', 'tap', str((a+c)//2), str((b+d)//2))
        return True
    return False


def main():
    report = {'scope': 'Original APK on disposable emulator; no account or private data', 'screens': [], 'settings_opened': False}
    try:
        install = adb('install', '-r', '--no-incremental', str(INPUT), timeout=240)
        if 'Success' not in install.splitlines():
            raise RuntimeError('Installation failed')
        adb('shell', 'am', 'start', '-n', f'{PACKAGE}/{ACTIVITY}')
        time.sleep(30)
        for step in range(7):
            nodes = dump()
            if any("isn't responding" in (n.get('text') or '').lower() for n in nodes):
                if click_label(nodes, 'Wait'):
                    adb('shell', 'am', 'start', '-n', f'{PACKAGE}/{ACTIVITY}')
                    time.sleep(12)
                    nodes = dump()
            clicked = maybe_click(nodes)
            report['screens'].append({'stage': f'initial-{step}', 'nodes': snapshot(nodes), 'clicked': clicked})
            if not clicked:
                break
            time.sleep(4)
        nodes = dump()
        if not click_label(nodes, 'Settings', lower_y=450):
            screenshot('settings-not-found')
            raise RuntimeError('Settings tab not found')
        report['settings_opened'] = True
        time.sleep(6)
        for stage in ('top', 'middle', 'bottom'):
            nodes = dump()
            report['screens'].append({'stage': stage, 'nodes': snapshot(nodes)})
            screenshot('settings-' + stage)
            adb('shell', 'input', 'swipe', '160', '530', '160', '180', '400')
            time.sleep(2)
    finally:
        OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print('Original Settings tab opened:', report['settings_opened'])


if __name__ == '__main__':
    main()
