#!/usr/bin/env python3
"""Test a re-signed Web fixture and synthetic Add Email UI on an empty emulator."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/telegram'))
from emulator_smoke import test_one  # noqa: E402

TARGET = 'org.telegram.messenger.web'
TEST_PACKAGE = 'app.morphe.telegramemailtest'
RUNNER = TEST_PACKAGE + '/.SyntheticEmailHarness'


def adb(*args: str, timeout: int = 120, required: bool = True) -> str:
    result = subprocess.run(['adb', *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, timeout=timeout)
    if required and result.returncode:
        raise RuntimeError('ADB command failed: ' + result.stdout[-2000:])
    return result.stdout


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit('usage: emulator_test.py experiment-test.apk synthetic-test.apk report.json')
    apk, harness, output = map(Path, sys.argv[1:])
    if not apk.is_file() or not harness.is_file():
        raise ValueError('Missing ephemeral emulator fixture')
    adb('uninstall', TEST_PACKAGE, required=False)
    launch = test_one('email-experiment-only', apk)
    installed = adb('install', '-r', str(harness), timeout=180)
    if 'Success' not in installed:
        raise RuntimeError('Synthetic instrumentation install failed')
    adb('shell', 'am', 'force-stop', TARGET)
    result = adb('shell', 'am', 'instrument', '-w', RUNNER, timeout=180)
    if ('INSTRUMENTATION_RESULT: synthetic_email_ui=passed_no_offer_and_server_offered_timeout' not in result or
            'INSTRUMENTATION_CODE: -1' not in result):
        raise RuntimeError('Synthetic UI instrumentation failed: ' + result[-3000:])
    report = {
        'outcome': 'passed',
        'fixture': launch,
        'synthetic_add_email_ui': 'passed_no_offer_and_server_offered_timeout',
        'synthetic_values_only_no_otp_or_login_request': True,
        'server_offer_and_real_login': 'not_tested',
        'payment_avoidance': 'not_tested_and_not_guaranteed',
        'physical_device_and_google_play_apk': 'not_tested',
    }
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
