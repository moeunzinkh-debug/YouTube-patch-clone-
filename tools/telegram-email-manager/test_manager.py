#!/usr/bin/env python3
"""Exercise a local MPP in a disposable Android emulator, without an account.

Only the stock Telegram Web APK and a verified Manager release are used; no login,
phone number, OTP, or external Telegram request is made by this test.
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUTS = Path('/tmp/telegram-email-manager')
SELECTOR = 'Try another login method (experimental)'
LAST_STAGE = 'startup'


def adb(*args: str, timeout: int = 90) -> str:
    result = subprocess.run(['adb', *args], text=True, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"adb {' '.join(args[:3])} failed: {result.stderr[-1200:]}")
    return result.stdout


def dump() -> list[dict[str, str]]:
    adb('shell', 'uiautomator', 'dump', '/sdcard/window.xml', timeout=45)
    raw = adb('exec-out', 'cat', '/sdcard/window.xml')
    root = ET.fromstring(raw)
    return [node.attrib for node in root.iter('node')]


def snapshot(nodes: list[dict[str, str]]) -> str:
    entries = []
    for n in nodes:
        label = n.get('text') or n.get('content-desc')
        if label and n.get('bounds'):
            entries.append(f"{label[:100]}@{n['bounds']}" + (f" checked={n['checked']}" if n.get('checkable') == 'true' else ''))
    return ' | '.join(entries)[:3500]


def announce(stage: str, nodes: list[dict[str, str]]) -> None:
    print(f'::notice title={stage}::{snapshot(nodes)}', flush=True)


def matches(n: dict[str, str], label: str, exact: bool = False) -> bool:
    values = [n.get('text', ''), n.get('content-desc', '')]
    return any((value == label if exact else label.casefold() in value.casefold()) for value in values)


def wait_for(label: str, seconds: int = 50, exact: bool = False) -> tuple[list[dict[str, str]], dict[str, str]]:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        nodes = dump()
        for n in nodes:
            if matches(n, label, exact) and re.fullmatch(r'\[\d+,\d+\]\[\d+,\d+\]', n.get('bounds', '')):
                return nodes, n
        time.sleep(1)
    raise RuntimeError(f'Could not find UI label: {label}')


def tap(label: str, seconds: int = 50, exact: bool = False) -> list[dict[str, str]]:
    nodes, node = wait_for(label, seconds, exact)
    bounds = [int(x) for x in re.findall(r'\d+', node['bounds'])]
    adb('shell', 'input', 'tap', str((bounds[0] + bounds[2]) // 2), str((bounds[1] + bounds[3]) // 2))
    return nodes


def media_id(name: str) -> str:
    end = time.monotonic() + 45
    while time.monotonic() < end:
        listing = adb('shell', 'content', 'query', '--uri', 'content://media/external/file', '--projection', '_id:_display_name')
        for line in listing.splitlines():
            if name in line:
                match = re.search(r'_id=(\d+)', line)
                if match:
                    return match.group(1)
        time.sleep(1)
    raise RuntimeError('Pushed local MPP was not indexed by MediaStore')


def main() -> None:
    global LAST_STAGE
    manager = INPUTS / 'morphe-manager-2.2.0.apk'
    telegram = INPUTS / 'Telegram-12.10.1.apk'
    bundle = ROOT / 'bundles/telegram-email-experimental/bundle.mpp'
    adb('install', '-r', str(manager), timeout=180)
    adb('install', '-r', str(telegram), timeout=180)
    adb('shell', 'am', 'start', '-n', 'app.morphe.manager/.MainActivity')
    time.sleep(15)
    LAST_STAGE = 'initial manager'
    announce(LAST_STAGE, dump())

    LAST_STAGE = 'import local source'
    name = 'telegram-email-experiment.mpp'
    adb('push', str(bundle), f'/sdcard/Download/{name}')
    adb('shell', 'am', 'broadcast', '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE', '-d', f'file:///sdcard/Download/{name}')
    bundle_id = media_id(name)
    adb('shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-t', 'application/vnd.ms-project',
        '--grant-read-uri-permission', '-d', f'content://media/external/file/{bundle_id}',
        '-n', 'app.morphe.manager/.MainActivity')
    nodes, _ = wait_for('Do you want to add this patch source to Morphe?', 45)
    announce('source confirmation', nodes)
    tap('Add', exact=True)
    time.sleep(12)
    announce('source added', dump())

    LAST_STAGE = 'enable expert mode'
    tap('Settings', exact=True)
    nodes, _ = wait_for('Expert mode', 35)
    announce('expert settings', nodes)
    tap('Expert mode', exact=True)
    nodes, _ = wait_for('Enable Expert mode?', 20)
    announce('expert confirmation', nodes)
    tap('Enable', exact=True)
    time.sleep(2)

    LAST_STAGE = 'open Telegram patch flow'
    adb('shell', 'am', 'start', '-a', 'app.morphe.manager.action.PATCH_APP',
        '--es', 'patch_package', 'org.telegram.messenger.web', '-n', 'app.morphe.manager/.MainActivity')
    time.sleep(8)
    announce('patch dialog', dump())
    # Subsequent steps are driven by the exact Manager screen hierarchy.
    raise RuntimeError('Manager patch flow inspection is not yet complete')


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
