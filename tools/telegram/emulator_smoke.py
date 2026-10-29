#!/usr/bin/env python3
"""Launch-test stock and re-signed patched Telegram on an empty Android emulator.

No account, phone number, login code, chat, token, or user data is supplied.
This only tests installation and process survival, not feature or push behavior.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

PACKAGE = 'org.telegram.messenger.web'


def run(*args: str, timeout: int = 40, required: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    if required and result.returncode:
        raise RuntimeError(f'{args[0]} command failed ({result.returncode}): {result.stdout[-1200:]}')
    return result


def parse_launcher(output: str) -> str:
    pattern = re.compile(r'^(' + re.escape(PACKAGE) + r'/[A-Za-z0-9_.$]+)$', re.MULTILINE)
    matches = pattern.findall(output)
    if len(matches) != 1:
        raise ValueError('Could not resolve a unique Telegram launcher activity')
    return matches[0]


def parse_pid(output: str) -> bool:
    return bool(re.fullmatch(r'\s*\d+(?:\s+\d+)*\s*', output))


def parse_start_status(output: str) -> str:
    match = re.search(r'^Status:\s*(\S+)', output, re.MULTILINE)
    return match.group(1).lower() if match else 'unknown'


def relevant_crash(log: str) -> str | None:
    lines = log.splitlines()
    for index, line in enumerate(lines):
        if 'Process: ' + PACKAGE not in line:
            continue
        block = lines[max(0, index - 2):index + 12]
        if not any('FATAL EXCEPTION' in item for item in block):
            continue
        clean = [item.strip() for item in block if any(word in item for word in
                 ('FATAL EXCEPTION', 'Process:', 'Exception', 'Caused by:', 'at org.telegram', 'at app.template'))]
        return '\n'.join(clean[:8])[:2500]
    return None


def test_one(label: str, apk: Path) -> dict:
    if not apk.is_file():
        raise ValueError('APK fixture does not exist: ' + label)
    run('adb', 'uninstall', PACKAGE, required=False)
    run('adb', 'logcat', '-c')
    install = run('adb', 'install', '-r', str(apk), timeout=180)
    if 'Success' not in install.stdout:
        raise RuntimeError('ADB did not confirm install success: ' + label)
    resolve = run('adb', 'shell', 'cmd', 'package', 'resolve-activity', '--brief',
                  '-a', 'android.intent.action.MAIN', '-c', 'android.intent.category.LAUNCHER', PACKAGE)
    launcher = parse_launcher(resolve.stdout)
    start = run('adb', 'shell', 'am', 'start', '-W', '-n', launcher, timeout=90)
    status = parse_start_status(start.stdout)
    if start.returncode or status != 'ok' or 'Error:' in start.stdout or 'Exception' in start.stdout:
        raise RuntimeError('Could not confirm launcher start: ' + start.stdout[-1200:])
    time.sleep(12)
    process = run('adb', 'shell', 'pidof', PACKAGE, required=False)
    logs = run('adb', 'logcat', '-d', '-s', 'AndroidRuntime:E', '*:S', required=False).stdout
    crash = relevant_crash(logs)
    window = run('adb', 'shell', 'dumpsys', 'window', 'windows', timeout=60, required=False).stdout
    activities = run('adb', 'shell', 'dumpsys', 'activity', 'activities', timeout=60, required=False).stdout
    focus_lines = [line.strip()[:350] for line in (window + '\n' + activities).splitlines()
                   if any(marker in line for marker in
                          ('mCurrentFocus=', 'mFocusedApp=', 'mResumedActivity:', 'topResumedActivity='))][:8]
    result = {
        'fixture': label,
        'install': 'passed',
        'launcher': launcher,
        'activity_manager_start_status': status,
        'process_alive_after_12_seconds': parse_pid(process.stdout),
        'telegram_reported_focused_or_resumed': any(PACKAGE in line for line in focus_lines),
        'focus_or_resume_diagnostics': focus_lines,
        'fatal_exception': crash,
    }
    if not result['process_alive_after_12_seconds'] or not result['telegram_reported_focused_or_resumed'] or crash:
        raise RuntimeError('Telegram did not remain running in the foreground: ' + json.dumps(result))
    return result


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit('usage: emulator_smoke.py original.apk remove-ads.apk all-default.apk report.json')
    original, single, all_default, output = map(Path, sys.argv[1:])
    report = {
        'scope': 'Ephemeral Android emulator, no account or messages; only install and launcher process survival.',
        'package': PACKAGE,
        'api_level': run('adb', 'shell', 'getprop', 'ro.build.version.sdk').stdout.strip(),
        'cases': [],
        'feature_behavior_login_push_and_real_device': 'not_tested',
    }
    try:
        run('adb', 'shell', 'input', 'keyevent', '82', required=False)
        # No personal account is configured; attempt to keep this synthetic test offline.
        report['wifi_disable_command'] = run('adb', 'shell', 'svc', 'wifi', 'disable', required=False).returncode == 0
        report['mobile_data_disable_command'] = run('adb', 'shell', 'svc', 'data', 'disable', required=False).returncode == 0
        for name, apk in [('original_telegram_signed', original), ('remove_ads_test_signed', single),
                          ('all_14_default_test_signed', all_default)]:
            report['cases'].append(test_one(name, apk))
        report['outcome'] = 'passed_launcher_process_smoke'
    except Exception as exc:
        report['outcome'] = 'failed_or_incomplete'
        report['error'] = str(exc)[:3000]
        raise
    finally:
        output.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
