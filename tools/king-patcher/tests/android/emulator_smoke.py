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
    try:
        result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        output = error.stdout or ''
        if isinstance(output, bytes): output = output.decode(errors='replace')
        raise RuntimeError(f'command timed out after {timeout}s: {args[:3]}\n{output[-5000:]}') from error
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


def launch_and_check(expected: tuple[str, ...], absent: tuple[str, ...] = (), package: str = PACKAGE) -> None:
    last = ''
    for _ in range(3):
        adb('shell', 'am', 'force-stop', package)
        start = adb('shell', 'am', 'start', '-W', '-n', package + '/.MainActivity', timeout=60)
        time.sleep(2)
        text = screen_text()
        # Google API emulator setup can briefly pop an ANR over the test app.
        # Do not mistake that unrelated system dialog for a fixture failure.
        if 'com.google.android.googlesdksetup' in text and "isn't responding" in text:
            adb('shell', 'am', 'force-stop', 'com.google.android.googlesdksetup')
            last = 'Google SDK setup ANR over fixture'; continue
        missing = [value for value in expected if value not in text]
        unexpected = [value for value in absent if value in text]
        if not missing and not unexpected: return
        last = f'missing={missing}, unexpected={unexpected}; launch={start[-1000:]!r}; screen={text[:1000]!r}'
    raise AssertionError('Fixture UI did not match after retries: ' + last)


def verify_signature(path: Path) -> str:
    dirs = sorted((Path(os.environ['ANDROID_HOME']) / 'build-tools').iterdir(), key=lambda p: [int(x) if x.isdigit() else x for x in re.split(r'([0-9]+)', p.name)])
    tools = dirs[-1]
    output = run(str(tools / 'apksigner'), 'verify', '--min-sdk-version', '23', '--print-certs', str(path), timeout=120)
    signers = {value.lower() for value in re.findall(r'certificate SHA-256 digest:\s*([0-9a-f]{64})', output, flags=re.IGNORECASE)}
    if len(signers) != 1: raise AssertionError('Expected one signer fingerprint; apksigner output: ' + output[-2500:])
    run(str(tools / 'zipalign'), '-c', '-P', '16', '4', str(path), timeout=120)
    return next(iter(signers))


def main() -> None:
    bundle = WORK.parent / 'king-bundle' / 'bundle.mpp'
    report = {'environment': 'Disposable Android emulator; synthetic APKs; original King release asset untouched',
              'bundle_sha256': hashlib.sha256(bundle.read_bytes()).hexdigest(),
              'king_package': TARGET, 'runtime': 'not completed', 'morphe_manager_ui': 'not tested',
              'king_menu_navigation': 'not tested end to end',
              'real_target_apps': 'not tested', 'system_file_picker': 'not tested'}
    try:
        adb('shell', 'input', 'keyevent', 'KEYCODE_WAKEUP')
        adb('shell', 'wm', 'dismiss-keyguard')
        for name in ('king.apk', 'harness.apk', 'fixture.apk', 'pairip-fixture.apk'):
            adb('install', '-r', str(WORK / name), timeout=120)
        adb('push', str(WORK / 'fixture.apk'), '/sdcard/Download/king-fixture.apk', timeout=120)
        adb('shell', 'am', 'broadcast', '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE', '-d',
            'file:///sdcard/Download/king-fixture.apk')
        launch_and_check(('DENIED-561', 'KEEP-ME', 'HIDE-ME', 'HIDE-EXISTING'))
        report['baseline_fixture'] = 'denied LVL callback and all fixture UI elements visible'
        launch_and_check(('PAIRIP-1-1',), package='test.king.pairip')
        report['baseline_pairip_fixture'] = 'both synthetic PairIP entry points ran before patching'
        instrument = adb('shell', 'am', 'instrument', '-w', '-r', 'test.king.harness/.KingInstrumentation', timeout=480)
        (WORK / 'instrument.log').write_text(instrument)
        if 'INSTRUMENTATION_RESULT: status=PASS' not in instrument or 'INSTRUMENTATION_CODE: -1' not in instrument:
            raise AssertionError('Instrumentation failed:\n' + instrument[-6000:])
        report['king_menu_navigation'] = 'renderer and both click listeners tested with synthetic rows; end-to-end navigation not tested'
        for mode in ('ui', 'lvl', 'pairip'):
            remote = f'/sdcard/Android/data/{TARGET}/files/king-{mode}-fixture.apk'
            saved = f'/sdcard/Download/king-{mode}-modified.apk'
            adb('pull', remote, str(WORK / f'{mode}-output.apk'), timeout=120)
            adb('pull', saved, str(WORK / f'{mode}-saved.apk'), timeout=120)
            if hashlib.sha256((WORK / f'{mode}-output.apk').read_bytes()).digest() != hashlib.sha256((WORK / f'{mode}-saved.apk').read_bytes()).digest():
                raise AssertionError('System picker output did not match verified APK: ' + mode)
        original = adb('shell', 'sha256sum', '/sdcard/Download/king-fixture.apk').split()[0]
        if original != hashlib.sha256((WORK / 'fixture.apk').read_bytes()).hexdigest():
            raise AssertionError('Original system-picker input was modified')
        report['system_file_picker'] = 'selected UI input and saved all three outputs in Downloads; saved bytes and original SHA-256 checked'
        ui_signer = verify_signature(WORK / 'ui-output.apk')
        lvl_signer = verify_signature(WORK / 'lvl-output.apk')
        pair_signer = verify_signature(WORK / 'pairip-output.apk')
        if len({ui_signer, lvl_signer, pair_signer}) != 1: raise AssertionError('Per-install signing key was not stable')
        report['signature'] = 'Android Keystore signed; v1/v2 verified at API 23+; same key for all outputs'
        report['alignment'] = 'zipalign verification passed including 16 KiB native alignment option'
        adb('uninstall', PACKAGE)
        adb('install', str(WORK / 'lvl-output.apk'), timeout=120)
        launch_and_check(('LICENSED-256', 'KEEP-ME', 'HIDE-ME', 'HIDE-EXISTING'), ('DENIED-561',))
        report['lvl_fixture'] = 'classic callback changed from denial to allow(256) on Android'
        report['dex_integrity'] = 'rewritten DEX SHA-1 and Adler-32 accepted by Android runtime'
        adb('uninstall', 'test.king.pairip')
        adb('install', str(WORK / 'pairip-output.apk'), timeout=120)
        launch_and_check(('PAIRIP-0-0',), ('PAIRIP-1-1',), package='test.king.pairip')
        report['pairip_fixture'] = 'automatic scan matched reviewed shape in classes2.dex and both synthetic entry points stopped running on Android'
        adb('uninstall', PACKAGE)
        adb('install', str(WORK / 'ui-output.apk'), timeout=120)
        launch_and_check(('DENIED-561', 'KEEP-ME'), ('HIDE-ME', 'HIDE-EXISTING'))
        report['ui_fixture'] = 'manually selected compiled views hidden with inserted and replaced visibility attributes; unrelated label remains visible'
        report['source_copy'] = 'instrumentation checked original synthetic APK SHA-256 unchanged'
        report['runtime'] = 'passed'
    except BaseException as error:
        report['runtime'] = 'failed'
        report['failure'] = str(error)[-6000:]
        try:
            log = adb('logcat', '-d', '-t', '800', timeout=30)
            relevant = [line for line in log.splitlines() if any(token in line for token in ('FATAL EXCEPTION', 'AndroidRuntime', 'NoSuchMethodError', 'NoClassDefFoundError', 'VerifyError'))]
            report['android_error_excerpt'] = relevant[-20:]
            crash = adb('logcat', '-b', 'crash', '-d', '-t', '300', timeout=30)
            report['crash_buffer_excerpt'] = crash[-10000:]
            report['king_launch_excerpt'] = [line[:400] for line in log.splitlines()
                if TARGET in line and any(word in line.lower() for word in ('start', 'display', 'activity', 'process', 'fatal', 'denied', 'blocked', 'died'))][-25:]
            state = adb('shell', 'dumpsys', 'activity', 'activities', timeout=15)
            report['king_activity_state'] = [line.strip()[:400] for line in state.splitlines()
                if TARGET in line or re.search(r'\* ActivityRecord\{', line)][-20:]
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
