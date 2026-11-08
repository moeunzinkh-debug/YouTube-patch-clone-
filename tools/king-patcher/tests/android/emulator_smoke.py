#!/usr/bin/env python3
"""Exercise a disposable King copy and synthetic app on an Android emulator."""
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

WORK = Path(sys.argv[1]).resolve()
REPORT = Path(sys.argv[2]).resolve()
PACKAGE = 'test.king.fixture'
TARGET = 'ru.jgaiecip.osuojvyxe'


def run(*args: str, timeout: int = 90) -> str:
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'command failed ({result.returncode}): {args[:3]}\n{result.stdout[-3000:]}')
    return result.stdout


def adb(*args: str, timeout: int = 90) -> str:
    return run('adb', *args, timeout=timeout)


def screen_text() -> str:
    last = ''
    for _ in range(12):
        try:
            adb('shell', 'uiautomator', 'dump', '/sdcard/king-window.xml', timeout=40)
            xml = adb('shell', 'cat', '/sdcard/king-window.xml', timeout=20)
            root = ET.fromstring(xml[xml.index('<?xml'):])
            return '\n'.join(node.attrib.get('text', '') for node in root.iter())
        except Exception as error:
            last = str(error)
            time.sleep(1)
    raise RuntimeError('Unable to read synthetic fixture screen: ' + last[-500:])


def launch_and_check(expected: tuple[str, ...], absent: tuple[str, ...] = ()) -> None:
    adb('shell', 'am', 'force-stop', PACKAGE)
    adb('shell', 'am', 'start', '-W', '-n', PACKAGE + '/.MainActivity', timeout=60)
    time.sleep(1)
    text = screen_text()
    for value in expected:
        if value not in text: raise AssertionError(f'Expected fixture UI text {value!r}: {text[:1000]}')
    for value in absent:
        if value in text: raise AssertionError(f'Unexpected fixture UI text {value!r}: {text[:1000]}')


def verify_signature(path: Path) -> str:
    dirs = sorted((Path(os.environ['ANDROID_HOME']) / 'build-tools').iterdir(), key=lambda p: [int(x) if x.isdigit() else x for x in re.split(r'([0-9]+)', p.name)])
    tools = dirs[-1]
    output = run(str(tools / 'apksigner'), 'verify', '--min-sdk-version', '23', '--print-certs', str(path), timeout=120)
    match = re.search(r'Signer #1 certificate SHA-256 digest: ([0-9a-f]+)', output, flags=re.IGNORECASE)
    if not match: raise AssertionError('No signer fingerprint')
    run(str(tools / 'zipalign'), '-c', '-P', '16', '4', str(path), timeout=120)
    return match.group(1).lower()


def main() -> None:
    report = {'environment': 'Disposable Android emulator; synthetic APKs; original King release asset untouched',
              'king_package': TARGET, 'runtime': 'not completed', 'morphe_manager_ui': 'not tested',
              'real_target_apps': 'not tested', 'system_file_picker': 'not tested'}
    try:
        adb('shell', 'input', 'keyevent', 'KEYCODE_WAKEUP')
        adb('shell', 'wm', 'dismiss-keyguard')
        for name in ('king.apk', 'harness.apk', 'fixture.apk'):
            adb('install', '-r', str(WORK / name), timeout=120)
        launch_and_check(('DENIED-561', 'KEEP-ME', 'HIDE-ME'))
        report['baseline_fixture'] = 'denied LVL callback and both UI elements visible'
        instrument = adb('shell', 'am', 'instrument', '-w', '-r', 'test.king.harness/.KingInstrumentation', timeout=360)
        (WORK / 'instrument.log').write_text(instrument)
        if 'INSTRUMENTATION_RESULT: status=PASS' not in instrument or 'INSTRUMENTATION_CODE: -1' not in instrument:
            raise AssertionError('Instrumentation failed:\n' + instrument[-6000:])
        for mode in ('ui', 'lvl'):
            remote = f'/sdcard/Android/data/{TARGET}/files/king-{mode}-fixture.apk'
            adb('pull', remote, str(WORK / f'{mode}-output.apk'), timeout=120)
        ui_signer = verify_signature(WORK / 'ui-output.apk')
        lvl_signer = verify_signature(WORK / 'lvl-output.apk')
        if ui_signer != lvl_signer: raise AssertionError('Per-install signing key was not stable')
        report['signature'] = 'Android Keystore signed; v1/v2 verified at API 23+; same key for both outputs'
        report['alignment'] = 'zipalign verification passed including 16 KiB native alignment option'
        adb('uninstall', PACKAGE)
        adb('install', str(WORK / 'lvl-output.apk'), timeout=120)
        launch_and_check(('LICENSED-256', 'KEEP-ME', 'HIDE-ME'), ('DENIED-561',))
        report['lvl_fixture'] = 'classic callback changed from denial to allow(256) on Android'
        adb('uninstall', PACKAGE)
        adb('install', str(WORK / 'ui-output.apk'), timeout=120)
        launch_and_check(('DENIED-561', 'KEEP-ME'), ('HIDE-ME',))
        report['ui_fixture'] = 'manually selected compiled button hidden; unrelated label remains visible'
        report['source_copy'] = 'instrumentation checked original synthetic APK SHA-256 unchanged'
        report['runtime'] = 'passed'
    except BaseException as error:
        report['runtime'] = 'failed'
        report['failure'] = str(error)[-6000:]
        try:
            log = adb('logcat', '-d', '-t', '800', timeout=30)
            relevant = [line for line in log.splitlines() if any(token in line for token in ('FATAL EXCEPTION', 'AndroidRuntime', 'NoSuchMethodError', 'NoClassDefFoundError', 'VerifyError'))]
            report['android_error_excerpt'] = relevant[-20:]
        except Exception:
            pass
        raise
    finally:
        report['run_url'] = f"https://github.com/{os.getenv('GITHUB_REPOSITORY', '')}/actions/runs/{os.getenv('GITHUB_RUN_ID', '')}"
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
        print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
