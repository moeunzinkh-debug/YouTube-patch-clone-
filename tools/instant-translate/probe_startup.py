#!/usr/bin/env python3
"""Compare startup of disposable emulator APKs without accounts or translations.

This intentionally uninstalls the target package between test APKs. It refuses to
run without explicit disposable-emulator opt-in and an Android emulator marker.
No real device, user data, API key or integrity-bypass modification is involved.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from probe_runtime import ACTIVITY, PACKAGE, adb, dump, maybe_click, snapshot

MESSAGE_KEYWORDS = ('signature', 'certificate', 'integrity', 'tamper', 'repack',
                    'license', 'unauthorized', 'security', 'checksum', 'signature mismatch')


def parse_crash_log(log: str) -> dict:
    """Extract exception classes and stack names, never arbitrary error messages."""
    lines = log.splitlines()
    starts = [i for i, line in enumerate(lines) if 'FATAL EXCEPTION' in line]
    blocks = []
    process = re.compile(r'\bProcess:\s*' + re.escape(PACKAGE) + r'(?::[\w.-]+)?(?:\s*,|\s*$)')
    for j, start in enumerate(starts):
        end = starts[j + 1] if j + 1 < len(starts) else len(lines)
        block = lines[start:min(end, start + 100)]
        if any(process.search(line) for line in block):
            blocks.append(block)
    exceptions, frames, keywords = [], [], set()
    for block in blocks:
        for line in block:
            kind = re.search(r'\b([\w.$]+(?:Exception|Error))(?::|\s*$)', line)
            frame = re.search(r'\bat ([\w.$]+)\(', line)
            if kind and kind.group(1) not in exceptions:
                exceptions.append(kind.group(1))
            if frame and frame.group(1) not in frames:
                frames.append(frame.group(1))
            message = re.search(r'\b[\w.$]+(?:Exception|Error):\s*(.*)', line)
            if message:
                lower = message.group(1).lower()
                keywords.update(keyword for keyword in MESSAGE_KEYWORDS if keyword in lower)
    return {'app_fatal_exception': bool(blocks), 'exception_types': exceptions[:12],
            'stack_frames': frames[:30], 'exception_message_keywords': sorted(keywords)}


def foreground_activity(dump_text: str) -> str:
    """Return a public component name only, not the rest of dumpsys output."""
    for line in dump_text.splitlines():
        if 'mResumedActivity' not in line and 'topResumedActivity' not in line:
            continue
        match = re.search(r'([\w.]+)/([\w.$]+)', line)
        if match:
            return match.group(0)
    return ''


def main() -> None:
    if os.environ.get('INSTANT_DISPOSABLE_EMULATOR') != '1' or adb('shell', 'getprop', 'ro.kernel.qemu') != '1':
        raise RuntimeError('This uninstalling probe runs only in an explicitly designated disposable emulator')
    path = Path(os.environ['INSTANT_STARTUP_APK'])
    output = Path(os.environ['INSTANT_STARTUP_REPORT'])
    mode = os.environ['INSTANT_STARTUP_MODE']
    if mode not in {'original', 'resigned_control', 'manager_patched'} or not path.is_file():
        raise ValueError('Unknown startup test mode or missing APK')
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        'scope': 'Disposable Android emulator; startup only; no account, text or API key',
        'mode': mode, 'package': PACKAGE,
        'abi_list': adb('shell', 'getprop', 'ro.product.cpu.abilist'),
        'native_bridge': adb('shell', 'getprop', 'ro.dalvik.vm.native.bridge'),
        'wifi_on': adb('shell', 'settings', 'get', 'global', 'wifi_on', check=False),
        'install': None, 'process_alive': False, 'main_activity_reached': False,
        'app_ui_visible': False, 'crash_dialog_seen': False, 'screens': [],
    }
    try:
        adb('shell', 'am', 'force-stop', PACKAGE, check=False)
        adb('shell', 'input', 'keyevent', 'KEYCODE_HOME', check=False)
        # Different signing certificates cannot be installed over one another.
        adb('uninstall', PACKAGE, timeout=120, check=False)
        report['install'] = adb('install', '--no-incremental', str(path), timeout=240)
        if 'Success' not in report['install'].splitlines():
            raise RuntimeError('Disposable emulator install did not succeed')
        adb('logcat', '-c', check=False)
        adb('logcat', '-b', 'crash', '-c', check=False)
        adb('shell', 'am', 'start', '-n', f'{PACKAGE}/{ACTIVITY}')
        time.sleep(30)
        for stage in range(8):
            nodes = dump()
            labels = [n.get('text', '') or n.get('content-desc', '') for n in nodes]
            report['crash_dialog_seen'] |= any('keeps stopping' in value.lower() for value in labels)
            focused = foreground_activity(adb('shell', 'dumpsys', 'activity', 'activities', check=False))
            report['main_activity_reached'] |= focused.endswith('/com.spaceship.screen.translate.ui.MainActivity')
            report['app_ui_visible'] |= any(n.get('package') == PACKAGE for n in nodes)
            clicked = maybe_click(nodes) if not report['crash_dialog_seen'] else None
            report['screens'].append({'stage': stage, 'foreground': focused,
                                      'nodes': snapshot(nodes), 'routine_button_clicked': clicked})
            if report['crash_dialog_seen'] or report['main_activity_reached']:
                break
            if clicked:
                time.sleep(4)
            elif stage < 2:
                time.sleep(8)
            else:
                break
        # A live process by itself is not evidence of successful Activity launch.
        time.sleep(3)
        report['process_alive'] = bool(adb('shell', 'pidof', PACKAGE, check=False))
        crash = adb('logcat', '-b', 'crash', '-d', '-v', 'brief', timeout=45, check=False)
        report.update(parse_crash_log(crash))
    finally:
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(f"Startup probe {mode}: main={report['main_activity_reached']} "
          f"fatal={report['app_fatal_exception']} crash_dialog={report['crash_dialog_seen']}")


if __name__ == '__main__':
    main()
