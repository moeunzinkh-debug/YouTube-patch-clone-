#!/usr/bin/env python3
"""Import the Instant Translate MPP and patch the supplied APK in a disposable Manager emulator.

No account is used, the app APK is not launched, and network is disabled.
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = Path('/tmp/instant-manager')
MANAGER = INPUT / 'morphe-manager-2.3.0-dev.3.apk'
APKS = INPUT / 'Instant.Translate-v7.5.00300-com.spaceship.screen.textcopy.apk'
BUNDLE = ROOT / 'bundles/instant-translate/bundle.mpp'
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
    important = {'Instant Translate APK availability', 'Android APK picker', 'Instant Translate patch selection',
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
        if any(matches(n, 'Translation fallback (Google, experimental)') for n in nodes):
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
                raise RuntimeError('Manager did not accept the expected APKS identity')
            time.sleep(2)
    raise RuntimeError('Patch selection did not open')


def save_patched_apk() -> Path:
    before = set(adb('shell', 'find', '/sdcard/Download', '/sdcard/Documents', '-maxdepth', '1', '-type', 'f', '-name', '*.apk').splitlines())
    tap('Save', exact=True)
    time.sleep(4)
    nodes, _ = wait_for('SAVE', 45, exact=True)
    announce('Android save picker', nodes)
    tap('SAVE', exact=True)
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        candidates = adb('shell', 'find', '/sdcard/Download', '/sdcard/Documents', '-maxdepth', '1', '-type', 'f', '-name', '*.apk').splitlines()
        new_files = [path for path in candidates if path not in before]
        if new_files:
            target = INPUT / 'manager-merged-patched.apk'
            adb('pull', new_files[-1].strip(), str(target), timeout=180)
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

    LAST_STAGE = 'import Instant Translate patch source'
    bundle_id = push_media(BUNDLE, 'instant-patches.mpp')
    adb('shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-t', 'application/vnd.ms-project',
        '--grant-read-uri-permission', '-d', f'content://media/external/file/{bundle_id}',
        '-n', 'app.morphe.manager/.MainActivity')
    nodes, _ = wait_for('Do you want to add this patch source to Morphe?', 50)
    announce('source confirmation', nodes)
    tap('Add', exact=True)
    time.sleep(12)

    LAST_STAGE = 'enable experimental target'
    tap('Sources', exact=True)
    nodes, _ = wait_for('Instant Translate patches (experimental)', 45)
    announce('source list', nodes)
    tap('Instant Translate patches (experimental)')
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
    push_media(APKS, 'instant-input.apk')
    tap('Apps', exact=True)
    nodes, _ = wait_for('Instant Translate', 60)
    announce('Instant Translate visible in Manager Apps', nodes)
    tap('Instant Translate', exact=True)
    nodes, _ = wait_for('No, I already have it', 60)
    announce('Instant Translate APK availability', nodes)
    tap('No, I already have it', exact=True)
    time.sleep(4)
    nodes = dump()
    if any(matches(n, 'Allow access to manage all files') for n in nodes):
        announce('Manager file access prompt', nodes)
        tap('Allow access to manage all files', exact=True)
        adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
        time.sleep(5)
        nodes = dump()
    announce('Android APK picker', nodes)
    if not any(matches(n, 'instant-input.apk') for n in nodes):
        # The system picker may start in Recent instead of Downloads.
        if any(matches(n, 'Show roots') for n in nodes):
            tap('Show roots')
        elif any(matches(n, 'Browse') for n in nodes):
            tap('Browse')
        nodes, _ = wait_for('Downloads', 30)
        announce('Android storage locations', nodes)
        tap('Downloads', exact=True)
    tap('instant-input.apk', seconds=45)
    nodes = wait_for_patch_selection()
    announce('Instant Translate patch selection', nodes)
    if any(matches(n, 'Translation fallback (Google, experimental)') and 'Enabled' in n.get('content-desc', '') for n in nodes):
        raise RuntimeError('Privacy-sensitive fallback should be off by default')
    tap('Translation fallback (Google, experimental)')
    time.sleep(2)
    nodes = dump()
    if not any(matches(n, 'Translation fallback (Google, experimental)') and 'Enabled' in n.get('content-desc', '') for n in nodes):
        raise RuntimeError('Opt-in fallback was not enabled: ' + snapshot(nodes)[:1000])
    # The final screen must also report exactly one applied patch; it is the
    # reliable cross-source count when Manager displays other source tabs.
    tap('Patch', exact=True)

    LAST_STAGE = 'patch the APK in Manager'
    deadline = time.monotonic() + 720
    while time.monotonic() < deadline:
        nodes = dump()
        if any(matches(n, 'Background patching protection') for n in nodes):
            tap('Not now', exact=True)
        elif (any(matches(n, 'Patched', exact=True) for n in nodes)
              and any(matches(n, '1 patch', exact=True) for n in nodes)
              and any(matches(n, 'Instant Translate patches (experimental)') for n in nodes)
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
    print(f'::notice::Manager saved patched output ({result.stat().st_size} bytes); no user account or app runtime used', flush=True)


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
