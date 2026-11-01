#!/usr/bin/env python3
"""Apply the checked-in YouTube bundle in a disposable, offline Manager emulator.

Only the Manager is installed. The stock and patched YouTube APKs are temporary
CI inputs/outputs: neither is installed, launched, uploaded, or committed.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(os.environ.get('RUNNER_TEMP', '/tmp')) / 'youtube-manager'
MANAGER = WORK / 'morphe-manager-2.3.0-dev.3.apk'
STOCK = WORK / 'stock.apk'
BUNDLE = ROOT / 'patch.mpp'
REQUIRED = ('Download post images', 'Search comments', 'Translate posts',
            'Niconico comments', 'Audio equalizer', 'Voice over translation')
STAGE = 'startup'


def adb(*args: str, timeout: int = 90) -> str:
    result = subprocess.run(['adb', *args], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"adb {' '.join(args[:3])} failed: {result.stderr[-800:]}")
    return result.stdout


def dump() -> list[dict[str, str]]:
    adb('shell', 'uiautomator', 'dump', '/sdcard/window.xml', timeout=45)
    return [n.attrib for n in ET.fromstring(adb('exec-out', 'cat', '/sdcard/window.xml')).iter('node')]


def matches(node: dict[str, str], label: str, exact: bool = False) -> bool:
    return any(value == label if exact else label.casefold() in value.casefold()
               for value in (node.get('text', ''), node.get('content-desc', '')))


def snapshot(nodes: list[dict[str, str]]) -> str:
    return ' | '.join(f"{(n.get('text') or n.get('content-desc', ''))[:100]}@{n.get('bounds', '')}"
                      for n in nodes if n.get('text') or n.get('content-desc'))[:2900]


def announce(stage: str, nodes: list[dict[str, str]]) -> None:
    print(f'::notice title={stage}::{snapshot(nodes)}', flush=True)


def wait_for(label: str, seconds: int = 60, exact: bool = False) -> tuple[list[dict[str, str]], dict[str, str]]:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        nodes = dump()
        for node in nodes:
            if matches(node, label, exact) and re.fullmatch(r'\[\d+,\d+\]\[\d+,\d+\]', node.get('bounds', '')):
                return nodes, node
        time.sleep(1)
    raise RuntimeError(f'Could not find UI label: {label}')


def tap(label: str, seconds: int = 60, exact: bool = False) -> list[dict[str, str]]:
    nodes, node = wait_for(label, seconds, exact)
    x1, y1, x2, y2 = (int(x) for x in re.findall(r'\d+', node['bounds']))
    adb('shell', 'input', 'tap', str((x1 + x2) // 2), str((y1 + y2) // 2))
    return nodes


def push_media(path: Path, name: str) -> str:
    adb('push', str(path), f'/sdcard/Download/{name}', timeout=360)
    adb('shell', 'am', 'broadcast', '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE',
        '-d', f'file:///sdcard/Download/{name}')
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        rows = adb('shell', 'content', 'query', '--uri', 'content://media/external/file',
                   '--projection', '_id:_display_name')
        for row in rows.splitlines():
            if name in row:
                match = re.search(r'_id=(\d+)', row)
                if match:
                    return match.group(1)
        time.sleep(1)
    raise RuntimeError(f'{name} was not indexed by MediaStore')


def patch_selection() -> list[dict[str, str]]:
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        nodes = dump()
        if any(matches(n, 'Search patches', exact=True) for n in nodes):
            return nodes
        for title in ('Split APK detected', 'Do you want to experiment?', 'Unverified APK'):
            if any(matches(n, title) for n in nodes):
                announce(title, nodes)
                tap('Proceed anyway', exact=True)
                time.sleep(2)
                break
        else:
            if any(matches(n, message) for n in nodes for message in
                   ('Unsupported Version', 'Wrong package selected', 'not a valid APK',
                    'This feature is only available')):
                announce('Unexpected Manager warning', nodes)
                raise RuntimeError('Manager did not accept the verified APK')
            time.sleep(2)
    raise RuntimeError('Patch selection did not open')


def verify_selected_patches() -> None:
    tap('Search patches', exact=True)
    time.sleep(2)
    for name in REQUIRED:
        nodes = dump()
        # On a cold emulator the search field is visible before it gets focus.
        field = next((n for n in nodes if n.get('class') == 'android.widget.EditText'), None)
        if field is None:
            field = next((n for n in nodes if n.get('text') == 'Search patches'), None)
        if not field or not re.fullmatch(r'\[\d+,\d+\]\[\d+,\d+\]', field.get('bounds', '')):
            raise RuntimeError('Search field missing: ' + snapshot(nodes))
        x1, y1, x2, y2 = (int(x) for x in re.findall(r'\d+', field['bounds']))
        adb('shell', 'input', 'tap', str((x1 + x2) // 2), str((y1 + y2) // 2))
        adb('shell', 'input', 'text', name.replace(' ', '%s'))
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            nodes = dump()
            # The card's accessibility description contains the patch name and state.
            cards = [n for n in nodes if name.casefold() in n.get('content-desc', '').casefold()]
            if any('Enabled' in n['content-desc'] for n in cards):
                break
            if any('Disabled' in n['content-desc'] for n in cards):
                raise RuntimeError(f'{name} is disabled in Manager: {snapshot(nodes)}')
            time.sleep(1)
        else:
            raise RuntimeError(f'{name} not shown in Manager: {snapshot(nodes)}')
        print(f'::notice::Manager selected {name}', flush=True)
        tap('Clear', exact=True)
        time.sleep(1)
    # The toggle, rather than the field placeholder, closes the search.
    nodes = dump()
    toggle = next(n for n in nodes if n.get('content-desc') == 'Search patches')
    x1, y1, x2, y2 = (int(x) for x in re.findall(r'\d+', toggle['bounds']))
    adb('shell', 'input', 'tap', str((x1 + x2) // 2), str((y1 + y2) // 2))
    time.sleep(2)


def save_patched_apk() -> Path:
    tap('Save', exact=True)
    nodes, _ = wait_for('SAVE', 45, exact=True)
    announce('Android save picker', nodes)
    tap('SAVE', exact=True)
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        files = adb('shell', 'find', '/sdcard/Download', '/sdcard/Documents', '-maxdepth', '1',
                    '-type', 'f', '-name', '*.apk').splitlines()
        files = [p for p in files if not p.endswith('/youtube-input.apk')]
        if files:
            output = WORK / 'manager-patched.apk'
            adb('pull', files[-1].strip(), str(output), timeout=360)
            if output.is_file() and output.stat().st_size > 1000000:
                return output
        time.sleep(2)
    raise RuntimeError('Could not find saved Manager output APK')


def main() -> None:
    global STAGE
    WORK.mkdir(parents=True, exist_ok=True)
    adb('install', '-r', str(MANAGER), timeout=180)
    adb('shell', 'svc', 'wifi', 'disable')
    adb('shell', 'svc', 'data', 'disable')
    adb('shell', 'am', 'start', '-n', 'app.morphe.manager/.MainActivity')
    time.sleep(15)

    STAGE = 'import development YouTube patch source'
    bundle_id = push_media(BUNDLE, 'youtube-patches.mpp')
    adb('shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-t', 'application/vnd.ms-project',
        '--grant-read-uri-permission', '-d', f'content://media/external/file/{bundle_id}',
        '-n', 'app.morphe.manager/.MainActivity')
    wait_for('Do you want to add this patch source to Morphe?', 60)
    tap('Add', exact=True)
    time.sleep(12)

    STAGE = 'enable Expert mode'
    tap('Settings', exact=True)
    wait_for('Expert mode', 45)
    tap('Expert mode', exact=True)
    wait_for('Enable Expert mode?', 30)
    tap('Enable', exact=True)
    time.sleep(2)

    STAGE = 'select stock YouTube APK'
    push_media(STOCK, 'youtube-input.apk')
    tap('Apps', exact=True)
    wait_for('YouTube', 90, exact=True)
    tap('YouTube', exact=True)
    nodes, _ = wait_for('No, I already have it', 90)
    announce('YouTube APK availability', nodes)
    if not any(matches(n, '21.30.216') for n in nodes) or not any(matches(n, 'Recommended') for n in nodes):
        raise RuntimeError('Manager did not show YouTube 21.30.216 as the recommended target')
    tap('No, I already have it', exact=True)
    time.sleep(4)
    nodes = dump()
    if any(matches(n, 'Allow access to manage all files') for n in nodes):
        tap('Allow access to manage all files', exact=True)
        adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
        time.sleep(5)
        nodes = dump()
    if not any(matches(n, 'youtube-input.apk') for n in nodes):
        if any(matches(n, 'Show roots') for n in nodes):
            tap('Show roots')
        elif any(matches(n, 'Browse') for n in nodes):
            tap('Browse')
        wait_for('Downloads', 30)
        tap('Downloads', exact=True)
    tap('youtube-input.apk', seconds=60)
    nodes = patch_selection()
    announce('Manager patch selection', nodes)

    STAGE = 'verify four new patches and custom patches selected'
    verify_selected_patches()
    tap('Patch', exact=True)

    STAGE = 'apply patches in Manager'
    deadline = time.monotonic() + 1200
    while time.monotonic() < deadline:
        nodes = dump()
        if any(matches(n, 'Background patching protection') for n in nodes):
            tap('Not now', exact=True)
        elif (any(matches(n, 'Patched', exact=True) for n in nodes)
              and any(matches(n, 'Save', exact=True) for n in nodes)):
            announce('Manager patch succeeded', nodes)
            break
        elif any(matches(n, 'Oops! Something went wrong') or matches(n, 'Patching failed') for n in nodes):
            raise RuntimeError('Manager reported patching failure')
        time.sleep(4)
    else:
        raise RuntimeError('Manager patching did not complete before the deadline')

    STAGE = 'save Manager output without installation'
    output = save_patched_apk()
    (WORK / 'selection.json').write_text(json.dumps({'manager': '2.3.0-dev.3', 'android': 'API 35 x86_64',
        'target': '21.30.216', 'requiredSelected': REQUIRED, 'savedBytes': output.stat().st_size,
        'appInstalledOrLaunched': False}, indent=2) + '\n')
    print('::notice::Manager saved a patched YouTube APK; it was not installed or launched.', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'::error title={STAGE}::{str(exc)[:900]}', flush=True)
        try:
            announce('failure screen', dump())
        except Exception:
            pass
        sys.exit(1)
