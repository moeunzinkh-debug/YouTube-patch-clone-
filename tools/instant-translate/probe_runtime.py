#!/usr/bin/env python3
"""Launch only the pinned, unpatched Instant Translate APK in a disposable emulator.

This probe uses no account and no private user data. It records ABI/bridge status,
installation, launch, and a filtered UI snapshot; it does not claim translation
works. Only routine onboarding buttons are clicked in the temporary emulator.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

INPUT = Path(os.environ.get('RUNNER_TEMP', '/tmp')) / 'instant-runtime-input.apk'
OUTPUT = Path(os.environ.get('RUNNER_TEMP', '/tmp')) / 'instant-runtime.json'
PACKAGE = 'com.spaceship.screen.textcopy'
ACTIVITY = 'com.spaceship.screen.translate.page.SplashActivity'
SAFE_LABEL = re.compile(r"[\w\s.,!?()'&+:/–—\-]{1,90}\Z", re.UNICODE)
ROUTINE = {'continue', 'get started', 'get start', 'next', 'skip', 'not now',
           'allow', 'allow notifications', 'got it', 'ok', 'agree', 'i agree'}


def adb(*args: str, timeout: int = 90, check: bool = True) -> str:
    result = subprocess.run(['adb', *args], text=True, capture_output=True, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError('ADB command failed at ' + ' '.join(args[:2]))
    return (result.stdout or '').strip()


def safe_label(value: str) -> str:
    value = re.sub(r'\s+', ' ', value.strip())
    if not value or not SAFE_LABEL.fullmatch(value):
        return ''
    if 'http' in value.lower() or '@' in value or re.search(r'\d{5,}', value):
        return ''
    return value


def dump() -> list[dict[str, str]]:
    adb('shell', 'uiautomator', 'dump', '/sdcard/window.xml', timeout=60)
    raw = adb('exec-out', 'cat', '/sdcard/window.xml', timeout=30)
    return [node.attrib for node in ET.fromstring(raw).iter('node')]


def snapshot(nodes: list[dict[str, str]]) -> list[dict[str, str]]:
    result = []
    for node in nodes:
        label = safe_label(node.get('text') or node.get('content-desc') or '')
        bounds = node.get('bounds', '')
        resource = node.get('resource-id', '')
        if resource and not re.fullmatch(r'[\w.]+:id/[\w.]+', resource):
            resource = ''
        if (label or resource or node.get('clickable') == 'true' or node.get('class') == 'android.widget.EditText') and re.fullmatch(r'\[\d+,\d+\]\[\d+,\d+\]', bounds):
            result.append({'label': label, 'id': resource, 'class': node.get('class', ''), 'bounds': bounds,
                           'clickable': node.get('clickable', ''), 'enabled': node.get('enabled', '')})
    return result[:90]


def maybe_click(nodes: list[dict[str, str]]) -> str | None:
    for node in nodes:
        label = safe_label(node.get('text') or node.get('content-desc') or '')
        bounds = node.get('bounds', '')
        if label.casefold() not in ROUTINE or not re.fullmatch(r'\[\d+,\d+\]\[\d+,\d+\]', bounds):
            continue
        if node.get('enabled') != 'true':
            continue
        x1, y1, x2, y2 = map(int, re.findall(r'\d+', bounds))
        adb('shell', 'input', 'tap', str((x1 + x2) // 2), str((y1 + y2) // 2))
        return label
    return None


def main() -> None:
    report = {'scope': 'Disposable emulator, unpatched input, no account or private text; only a synthetic hola fixture',
              'package': PACKAGE, 'asset_sha256': 'f341a1b174bda7b5d1c95cb2fc84da238228a116844069ee962220acaf1e4e4c',
              'abi_list': adb('shell', 'getprop', 'ro.product.cpu.abilist'),
              'native_bridge': adb('shell', 'getprop', 'ro.dalvik.vm.native.bridge'),
              'install': None, 'launch_command': None, 'process_alive': False, 'fixture_submitted': False, 'screens': []}
    try:
        report['install'] = adb('install', '-r', str(INPUT), timeout=240)
        adb('logcat', '-c')
        report['launch_command'] = adb('shell', 'am', 'start', '-n', f'{PACKAGE}/{ACTIVITY}')
        time.sleep(30)
        for stage in range(7):
            nodes = dump()
            if any("isn't responding" in (n.get('text') or '').lower() for n in nodes):
                wait = next((n for n in nodes if n.get('text') == 'Wait'), None)
                if wait and re.fullmatch(r'\[\d+,\d+\]\[\d+,\d+\]', wait.get('bounds', '')):
                    a, b, c, d = map(int, re.findall(r'\d+', wait['bounds']))
                    adb('shell', 'input', 'tap', str((a+c)//2), str((b+d)//2))
                    adb('shell', 'am', 'start', '-n', f'{PACKAGE}/{ACTIVITY}')
                    time.sleep(12)
                    nodes = dump()
            clicked = maybe_click(nodes)
            report['screens'].append({'stage': stage, 'nodes': snapshot(nodes), 'routine_button_clicked': clicked})
            if not clicked:
                break
            time.sleep(4)
        # The bottom Translate tab opens a direct text-translation screen; do not
        # click Home's Start control, which launches the overlay-permission flow.
        nodes = dump()
        for node in nodes:
            if (safe_label(node.get('text') or node.get('content-desc') or '') == 'Translate' and
                    re.fullmatch(r'\[\d+,\d+\]\[\d+,\d+\]', node.get('bounds', ''))):
                x1, y1, x2, y2 = map(int, re.findall(r'\d+', node['bounds']))
                if y1 > 450:
                    adb('shell', 'input', 'tap', str((x1+x2)//2), str((y1+y2)//2))
                    time.sleep(5)
                    nodes = dump()
                    report['screens'].append({'stage': 'translate_tab', 'nodes': snapshot(nodes),
                                              'routine_button_clicked': 'Translate tab'})
                    # Select a known source language rather than depending on an
                    # unrelated language-detection model for the synthetic test.
                    source = next((n for n in nodes if safe_label(n.get('text', '')) == 'Detect Language'), None)
                    if source:
                        a, b, c, d = map(int, re.findall(r'\d+', source['bounds']))
                        adb('shell', 'input', 'tap', str((a+c)//2), str((b+d)//2))
                        time.sleep(3)
                        picker = dump()
                        report['screens'].append({'stage': 'source_picker', 'nodes': snapshot(picker),
                                                  'routine_button_clicked': 'Detect Language'})
                        screen = subprocess.run(['adb', 'exec-out', 'screencap', '-p'], capture_output=True, timeout=30, check=True)
                        (OUTPUT.parent / 'instant-source-screen.png').write_bytes(screen.stdout)
                        spanish = next((n for n in picker if safe_label(n.get('text', '')) == 'Spanish'), None)
                        if not spanish:
                            edit = next((n for n in picker if n.get('class') == 'android.widget.EditText'), None)
                            if edit:
                                a, b, c, d = map(int, re.findall(r'\d+', edit['bounds']))
                                adb('shell', 'input', 'tap', str((a+c)//2), str((b+d)//2))
                                adb('shell', 'input', 'text', 'Spanish')
                                time.sleep(3)
                                picker = dump()
                                report['screens'].append({'stage': 'source_search', 'nodes': snapshot(picker),
                                                          'routine_button_clicked': None})
                                spanish = next((n for n in picker if safe_label(n.get('text', '')) == 'Spanish'), None)
                        if spanish:
                            a, b, c, d = map(int, re.findall(r'\d+', spanish['bounds']))
                            adb('shell', 'input', 'tap', str((a+c)//2), str((b+d)//2))
                            time.sleep(3)
                        else:
                            adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
                            time.sleep(2)
                        nodes = dump()
                        report['screens'].append({'stage': 'source_selected', 'nodes': snapshot(nodes),
                                                  'routine_button_clicked': 'Spanish' if spanish else None})
                    # Use only a synthetic Spanish fixture. No user account,
                    # clipboard or personal text is involved.
                    for entry in nodes:
                        if (safe_label(entry.get('text', '')) == 'Enter text' and
                                re.fullmatch(r'\[\d+,\d+\]\[\d+,\d+\]', entry.get('bounds', ''))):
                            a, b, c, d = map(int, re.findall(r'\d+', entry['bounds']))
                            adb('shell', 'input', 'tap', str((a+c)//2), str((b+d)//2))
                            time.sleep(4)
                            editing = dump()
                            report['screens'].append({'stage': 'text_entry', 'nodes': snapshot(editing),
                                                      'routine_button_clicked': 'Enter text'})
                            if any(n.get('class') == 'android.widget.EditText' for n in editing):
                                adb('shell', 'input', 'text', 'hola')
                                time.sleep(2)
                                report['screens'].append({'stage': 'fixture_entered', 'nodes': snapshot(dump()),
                                                          'routine_button_clicked': None})
                                screen = subprocess.run(['adb', 'exec-out', 'screencap', '-p'], capture_output=True, timeout=30, check=True)
                                (OUTPUT.parent / 'instant-screen.png').write_bytes(screen.stdout)
                                # The emulator's IME has an action arrow at the
                                # bottom-right. KEYCODE_ENTER inserts a newline
                                # instead, so tap the visible IME action.
                                adb('shell', 'input', 'tap', '294', '590')
                                report['fixture_submitted'] = True
                                time.sleep(20)
                                report['screens'].append({'stage': 'fixture_submitted', 'nodes': snapshot(dump()),
                                                          'routine_button_clicked': 'keyboard action arrow'})
                                screen = subprocess.run(['adb', 'exec-out', 'screencap', '-p'], capture_output=True, timeout=30, check=True)
                                (OUTPUT.parent / 'instant-result-screen.png').write_bytes(screen.stdout)
                            break
                    break
        report['process_alive'] = bool(adb('shell', 'pidof', PACKAGE, check=False))
    finally:
        OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    if 'Success' not in (report['install'] or '').splitlines() or not report['process_alive']:
        raise RuntimeError('APK did not remain running; see sanitized runtime report')
    print('APK installed and launched in disposable emulator; fixture submitted:', report['fixture_submitted'])


if __name__ == '__main__':
    main()
