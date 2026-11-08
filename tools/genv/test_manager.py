#!/usr/bin/env python3
"""Import the GenV MPP and patch the supplied base APK in a disposable Manager emulator.

The input is an incomplete base APK. No GenV account is used, no app is launched, and network is disabled.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = Path('/tmp/genv-manager')
MANAGER = INPUT / os.environ.get('GENV_MANAGER_FILE', 'morphe-manager-2.3.0-dev.3.apk')
APK = INPUT / os.environ.get('GENV_INPUT_FILE', 'GenV_3.7.2.apk')
MEDIA_NAME = 'genv-input' + APK.suffix
BUNDLE = INPUT / 'bundle.mpp'
MICROG_ONLY = os.environ.get('GENV_MICROG_ONLY') == '1'
LAST_STAGE = 'startup'


def adb(*args: str, timeout: int = 90) -> str:
    result = subprocess.run(['adb', *args], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"adb {' '.join(args[:3])} failed: {result.stderr[-1000:]}")
    return result.stdout


def dump() -> list[dict[str, str]]:
    adb('shell', 'uiautomator', 'dump', '/sdcard/window.xml', timeout=45)
    return [node.attrib for node in ET.fromstring(adb('exec-out', 'cat', '/sdcard/window.xml')).iter('node')]


def matches(node: dict[str, str], label: str, exact: bool = False) -> bool:
    values = (node.get('text', ''), node.get('content-desc', ''))
    return any(value == label if exact else label.casefold() in value.casefold() for value in values)


def snapshot(nodes: list[dict[str, str]]) -> str:
    parts = []
    for node in nodes:
        label = node.get('text') or node.get('content-desc')
        if label and node.get('bounds'):
            checked = f" checked={node['checked']}" if node.get('checkable') == 'true' else ''
            parts.append(f"{label[:100]}@{node['bounds']}{checked}")
    return ' | '.join(parts)[:3500]


def announce(stage: str, nodes: list[dict[str, str]]) -> None:
    # Actions keeps only a small number of annotations per step. Reserve those
    # for the consequential screens and failures; retain the rest in the log.
    important = {'GenV APK availability', 'Android APK picker', 'GenV patch selection',
                 'Manager patch succeeded', 'Android save picker', 'failure screen',
                 'Unexpected Manager warning', 'Split APK detected',
                 'Do you want to experiment?', 'Unverified APK'}
    line = snapshot(nodes)
    if stage in important:
        print(f'::notice title={stage}::{line}', flush=True)
    else:
        print(f'{stage}: {line}', flush=True)


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


def media_id(name: str) -> str:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        rows = adb('shell', 'content', 'query', '--uri', 'content://media/external/file', '--projection', '_id:_display_name')
        for row in rows.splitlines():
            if name in row:
                match = re.search(r'_id=(\d+)', row)
                if match:
                    return match.group(1)
        time.sleep(1)
    raise RuntimeError(f'{name} was not indexed by MediaStore')


def push_media(path: Path, name: str) -> str:
    adb('push', str(path), f'/sdcard/Download/{name}', timeout=180)
    adb('shell', 'am', 'broadcast', '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE', '-d', f'file:///sdcard/Download/{name}')
    return media_id(name)


def wait_for_patch_selection() -> list[dict[str, str]]:
    deadline = time.monotonic() + 150
    announced = set()
    while time.monotonic() < deadline:
        nodes = dump()
        if any(matches(n, 'Remove license check') for n in nodes):
            return nodes
        for title in ('Split APK detected', 'Do you want to experiment?', 'Unverified APK'):
            if any(matches(n, title) for n in nodes):
                if title not in announced:
                    announce(title, nodes)
                    announced.add(title)
                tap('Proceed anyway', exact=True)
                time.sleep(2)
                break
        else:
            failures = ('Unsupported Version', 'Wrong package selected', 'not a valid APK', 'This feature is only available')
            if any(matches(node, message) for node in nodes for message in failures):
                announce('Unexpected Manager warning', nodes)
                raise RuntimeError('Manager did not accept the expected APK identity')
            time.sleep(2)
    raise RuntimeError('Patch selection did not open')


def save_patched_apk() -> Path:
    # Fresh Android 10 images do not always have a Documents directory yet;
    # find exits nonzero for a missing search root even when Downloads exists.
    adb('shell', 'mkdir', '-p', '/sdcard/Documents')
    tap('Save', exact=True)
    time.sleep(4)
    nodes, _ = wait_for('SAVE', 45, exact=True)
    announce('Android save picker', nodes)
    tap('SAVE', exact=True)
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        candidates = adb('shell', 'find', '/sdcard/Download', '/sdcard/Documents', '-maxdepth', '1', '-type', 'f', '-name', '*.apk').splitlines()
        candidates = [x for x in candidates if not x.endswith('/' + MEDIA_NAME)]
        if candidates:
            target = INPUT / 'manager-patched-base.apk'
            adb('pull', candidates[-1].strip(), str(target), timeout=180)
            if target.is_file() and target.stat().st_size > 1000000:
                return target
        time.sleep(2)
    raise RuntimeError('Could not find saved Manager output APK in Downloads')


def main() -> None:
    global LAST_STAGE
    INPUT.mkdir(parents=True, exist_ok=True)
    adb('install', '-r', str(MANAGER), timeout=180)
    adb('shell', 'svc', 'wifi', 'disable')
    adb('shell', 'svc', 'data', 'disable')
    adb('shell', 'am', 'start', '-n', 'app.morphe.manager/.MainActivity')
    time.sleep(15)
    announce('initial Manager', dump())

    LAST_STAGE = 'import GenV patch source'
    bundle_id = push_media(BUNDLE, 'genv-patches.mpp')
    adb('shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-t', 'application/vnd.ms-project',
        '--grant-read-uri-permission', '-d', f'content://media/external/file/{bundle_id}',
        '-n', 'app.morphe.manager/.MainActivity')
    nodes, _ = wait_for('Do you want to add this patch source to Morphe?', 50)
    announce('source confirmation', nodes)
    tap('Add', exact=True)
    time.sleep(12)

    LAST_STAGE = 'enable experimental target'
    tap('Sources', exact=True)
    nodes, _ = wait_for('GenV patches (experimental)', 45)
    announce('source list', nodes)
    tap('GenV patches (experimental)')
    nodes, _ = wait_for('Experimental app versions', 45)
    announce('experimental version toggle', nodes)
    tap('Experimental app versions', exact=True)
    time.sleep(3)
    announce('after enabling experimental target', dump())

    LAST_STAGE = 'enable expert mode'
    tap('Settings', exact=True)
    nodes, _ = wait_for('Expert mode', 45)
    announce('Manager settings', nodes)
    tap('Expert mode', exact=True)
    nodes, _ = wait_for('Enable Expert mode?', 30)
    announce('expert mode confirmation', nodes)
    tap('Enable', exact=True)
    time.sleep(2)

    LAST_STAGE = 'open supplied APK in Manager'
    push_media(APK, MEDIA_NAME)
    tap('Apps', exact=True)
    nodes, _ = wait_for('GenV', 60)
    announce('GenV visible in Manager Apps', nodes)
    tap('GenV', exact=True)
    nodes, _ = wait_for('No, I already have it', 60)
    announce('GenV APK availability', nodes)
    tap('No, I already have it', exact=True)
    time.sleep(4)
    nodes = dump()
    if any(matches(n, 'Allow Morphe to access photos, media, and files') for n in nodes):
        # Android 10 shows the legacy storage permission before the picker.
        tap('Allow', exact=True)
        time.sleep(4)
        nodes = dump()
    if any(matches(n, 'Allow access to manage all files') for n in nodes):
        announce('Manager file access prompt', nodes)
        tap('Allow access to manage all files', exact=True)
        adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
        time.sleep(5)
        nodes = dump()
    announce('Android APK picker', nodes)
    if not any(matches(n, MEDIA_NAME) for n in nodes):
        # The system picker may start in Recent instead of Downloads.
        if any(matches(n, 'Show roots') for n in nodes):
            tap('Show roots')
        elif any(matches(n, 'Browse') for n in nodes):
            tap('Browse')
        nodes, _ = wait_for('Downloads', 30)
        announce('Android storage locations', nodes)
        tap('Downloads', exact=True)
    tap(MEDIA_NAME, seconds=45)
    nodes = wait_for_patch_selection()
    announce('GenV patch selection', nodes)
    if not any(matches(n, 'Remove license check') and 'Enabled' in n.get('content-desc', '') for n in nodes):
        raise RuntimeError('GenV license-check patch was not enabled: ' + snapshot(nodes)[:1000])
    if MICROG_ONLY:
        tap('Remove license check', exact=False)
        time.sleep(2)
        nodes = dump()
        if any(matches(n, 'Remove license check') and 'Enabled' in n.get('content-desc', '') for n in nodes):
            raise RuntimeError('Could not deselect license patch: ' + snapshot(nodes)[:1000])
    microg = 'Morphe MicroG Google sign-in support (experimental)'
    if not any(matches(n, microg) for n in nodes):
        # Patch lists can be vertically scrollable on the emulator.
        adb('shell', 'input', 'swipe', '160', '480', '160', '250', '500')
        time.sleep(2)
        nodes = dump()
    if not any(matches(n, microg) for n in nodes):
        adb('shell', 'input', 'swipe', '160', '250', '160', '480', '500')
        time.sleep(2)
        nodes = dump()
    if not any(matches(n, microg) for n in nodes):
        raise RuntimeError('New MicroG selector is not visible: ' + snapshot(nodes)[:1200])
    if any(matches(n, microg) and 'Enabled' in n.get('content-desc', '') for n in nodes):
        raise RuntimeError('MicroG selector was unexpectedly enabled by default')
    tap(microg, exact=False)
    time.sleep(2)
    nodes = dump()
    if not any(matches(n, microg) and 'Enabled' in n.get('content-desc', '') for n in nodes):
        raise RuntimeError('Could not select the opt-in MicroG patch: ' + snapshot(nodes)[:1200])
    # The final screen reports the selected count across all source tabs.
    tap('Patch', exact=True)

    LAST_STAGE = 'patch the base APK in Manager'
    deadline = time.monotonic() + 720
    while time.monotonic() < deadline:
        nodes = dump()
        if any(matches(n, 'Background patching protection') for n in nodes):
            tap('Not now', exact=True)
        elif (any(matches(n, 'Patched', exact=True) for n in nodes)
              and any(matches(n, '1 patch' if MICROG_ONLY else '2 patches', exact=True) for n in nodes)
              and any(matches(n, 'GenV patches (experimental)') for n in nodes)
              and any(matches(n, 'Save', exact=True) for n in nodes)):
            announce('Manager patch succeeded', nodes)
            break
        elif any(matches(n, 'Oops! Something went wrong') or matches(n, 'Patching failed') for n in nodes):
            raise RuntimeError('Manager reported patching failure')
        time.sleep(4)
    else:
        raise RuntimeError('Manager patching did not complete before the deadline')

    LAST_STAGE = 'save patched APK from Manager'
    result = save_patched_apk()
    print(f'::notice::Manager saved the incomplete patched base ({result.stat().st_size} bytes); no GenV account or runtime used', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'::error title={LAST_STAGE}::{str(exc)[:900]}', flush=True)
        try:
            announce('failure screen', dump())
        except Exception:
            pass
        sys.exit(1)
