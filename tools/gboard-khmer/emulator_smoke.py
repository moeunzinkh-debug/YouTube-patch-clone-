#!/usr/bin/env python3
"""Exercise the actual MPP's Khmerlish code in a disposable Android emulator.

The emulator has a synthetic editor only. No real user input is read and no
APK, screenshot, or arbitrary log is published. The third-party-derived hybrid
is not stock Gboard. An IME may need Google services or ARM translation, so an
unavailable environment is reported as such rather than as a passing test.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/gboard-translate'))
import emulator_smoke as common  # noqa: E402

PACKAGE = common.PACKAGE
EDITOR_PACKAGE = 'dev.arena.khmerprobe'
EDITOR_ACTIVITY = 'dev.arena.khmerprobe.AndroidKhmerProbeActivity'
INSPECTOR_PACKAGE = common.INSPECTOR_PACKAGE
TARGET_INSPECTOR_PACKAGE = 'dev.arena.gboardtargetprobe'
TARGET_INSPECTOR = 'dev.arena.khmerprobe.AndroidGboardInspector'
PREF_KEY = 'pref_khmerlish_to_khmer_enabled'


def build_probes(tmp: Path, fixture_keystore: Path) -> None:
    sdk = Path(os.environ['ANDROID_HOME'])
    android_jar = sdk / 'platforms/android-35/android.jar'
    tools = max((sdk / 'build-tools').iterdir(), key=lambda p: tuple(int(x) for x in re.findall(r'\d+', p.name)))
    classes, dex = tmp / 'classes', tmp / 'dex'
    classes.mkdir()
    dex.mkdir()
    common.run('javac', '-source', '8', '-target', '8', '-encoding', 'UTF-8', '-cp', str(android_jar),
        '-d', str(classes), str(ROOT / 'tools/gboard-khmer/AndroidKhmerProbeActivity.java'),
        str(ROOT / 'tools/gboard-khmer/AndroidGboardInspector.java'),
        str(ROOT / 'tools/gboard-translate/AndroidWindowInspector.java'), timeout=90)
    common.run(str(tools / 'd8'), '--min-api', '26', '--lib', str(android_jar), '--output', str(dex),
        *sorted(map(str, classes.rglob('*.class'))), timeout=90)
    # The target inspector must have the same temporary test signature as the
    # synthetic Gboard fixture; this keystore is generated only for this run.
    key = fixture_keystore
    if not key.is_file():
        raise RuntimeError('Disposable fixture signing key is unavailable')
    manifests = {
        'editor': f'''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="{EDITOR_PACKAGE}">
            <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="32" />
            <application android:label="Synthetic Khmerlish test">
            <activity android:name="{EDITOR_ACTIVITY}" android:exported="true" />
            </application></manifest>''',
        'inspector': f'''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="{INSPECTOR_PACKAGE}">
            <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="32" />
            <application android:label="Synthetic keyboard inspector" />
            <instrumentation android:name="{common.INSPECTOR_RUNNER}" android:targetPackage="{INSPECTOR_PACKAGE}" />
            </manifest>''',
        'target_inspector': f'''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="{TARGET_INSPECTOR_PACKAGE}">
            <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="32" />
            <application android:label="Disposable Gboard inspector" />
            <instrumentation android:name="{TARGET_INSPECTOR}" android:targetPackage="{PACKAGE}" />
            </manifest>''',
    }
    for name, manifest_xml in manifests.items():
        manifest_dir = tmp / name
        manifest_dir.mkdir()
        manifest = manifest_dir / 'AndroidManifest.xml'
        manifest.write_text(manifest_xml, encoding='utf-8')
        unsigned, aligned, signed = (tmp / f'{name}-{suffix}.apk' for suffix in ('unsigned', 'aligned', 'signed'))
        common.run(str(tools / 'aapt'), 'package', '-f', '-M', str(manifest), '-I', str(android_jar), '-F', str(unsigned))
        with zipfile.ZipFile(unsigned, 'a') as archive:
            archive.write(dex / 'classes.dex', 'classes.dex')
        common.run(str(tools / 'zipalign'), '-f', '4', str(unsigned), str(aligned))
        common.run(str(tools / 'apksigner'), 'sign', '--ks', str(key), '--ks-pass', 'pass:android',
            '--key-pass', 'pass:android', '--out', str(signed), str(aligned), timeout=45)
        common.run('adb', 'install', '-r', str(signed), timeout=90)


def target_diagnostic(enable: bool = False, open_settings: bool = False) -> dict:
    command = ['adb', 'shell', 'am', 'instrument', '-w', '-r']
    if enable:
        command.extend(['-e', 'enable', 'true'])
    if open_settings:
        command.extend(['-e', 'open_settings', 'true'])
    command.append(f'{TARGET_INSPECTOR_PACKAGE}/{TARGET_INSPECTOR}')
    output = common.run(*command, timeout=90)
    match = re.search(r'^INSTRUMENTATION_RESULT: diagnostic=([A-Za-z0-9+/=]+)$', output, re.MULTILINE)
    if not match:
        raise RuntimeError('Same-signature Gboard diagnostic did not return a result')
    return json.loads(base64.b64decode(match.group(1)).decode('utf-8'))


def install_and_select(apk: Path, report: dict) -> None:
    common.run('adb', 'install', '-r', str(apk), timeout=180)
    report['fixture_install'] = 'passed'
    deadline = time.monotonic() + 30
    candidates = []
    while time.monotonic() < deadline:
        methods = common.run('adb', 'shell', 'ime', 'list', '-s', '-a')
        candidates = [x.strip() for x in methods.splitlines() if x.strip().startswith(PACKAGE + '/')]
        if candidates:
            break
        time.sleep(2)
    if len(candidates) != 1:
        raise RuntimeError(f'Expected one test IME component, found {len(candidates)}')
    ime = candidates[0]
    common.run('adb', 'shell', 'ime', 'enable', ime)
    common.run('adb', 'shell', 'ime', 'set', ime)
    common.run('adb', 'shell', 'settings', 'put', 'secure', 'show_ime_with_hard_keyboard', '1')
    if common.run('adb', 'shell', 'settings', 'get', 'secure', 'default_input_method') != ime:
        raise RuntimeError('Test IME was not selected')
    report['ime_selected'] = 'passed'


def open_editor() -> None:
    common.run('adb', 'shell', 'am', 'start', '-S', '-n', f'{EDITOR_PACKAGE}/{EDITOR_ACTIVITY}')
    time.sleep(5)
    for node in ET.fromstring(common.dump_ui()).iter('node'):
        if node.get('package') == EDITOR_PACKAGE and node.get('class') == 'android.widget.EditText':
            position = common.center(node.get('bounds', ''))
            if position:
                common.run('adb', 'shell', 'input', 'tap', *map(str, position))
            return
    raise RuntimeError('Synthetic editor did not open')


def editor_text() -> str:
    for node in ET.fromstring(common.dump_ui()).iter('node'):
        if node.get('package') == EDITOR_PACKAGE and node.get('class') == 'android.widget.EditText':
            return node.get('text', '')
    raise RuntimeError('Synthetic editor was not found')


def swipe_down_page() -> None:
    sizes = re.findall(r'(\d+)x(\d+)', common.run('adb', 'shell', 'wm', 'size'))
    if not sizes:
        raise RuntimeError('Emulator screen size is unavailable')
    width, height = map(int, sizes[-1])
    common.run('adb', 'shell', 'input', 'swipe', str(width // 2), str(int(height * .80)),
               str(width // 2), str(int(height * .27)), '450')
    time.sleep(1)


def find_and_tap(label: str, scroll: bool = True) -> bool:
    for attempt in range(6):
        for node in ET.fromstring(common.dump_ui()).iter('node'):
            text = node.get('text', '') + ' ' + node.get('content-desc', '')
            if label.lower() in text.lower():
                position = common.center(node.get('bounds', ''))
                if position:
                    common.run('adb', 'shell', 'input', 'tap', *map(str, position))
                    time.sleep(2)
                    return True
        if not scroll:
            return False
        swipe_down_page()
    return False


def labels() -> list[str]:
    return [n.get('text', '')[:100] for n in ET.fromstring(common.dump_ui()).iter('node')
            if n.get('text', '').strip()][:60]


def disable_autocorrect(report: dict) -> None:
    # Match the documented usage: Gboard must not replace Roman words first.
    if not find_and_tap('Corrections & suggestions', scroll=False):
        report['autocorrect'] = 'correction settings not located'
        return
    report['corrections_labels'] = labels()
    for _ in range(6):
        root = ET.fromstring(common.dump_ui())
        parents = {child: parent for parent in root.iter() for child in parent}
        title = next((n for n in root.iter('node')
                      if 'auto-correction' in n.get('text', '').lower()), None)
        if title is not None:
            group = title
            for _ in range(4):
                switches = [n for n in group.iter('node') if n.get('class', '').endswith('Switch')]
                if switches:
                    switch = switches[0]
                    bounds = switch.get('bounds', '')
                    if switch.get('checked') == 'true':
                        position = common.center(bounds)
                        if position:
                            common.run('adb', 'shell', 'input', 'tap', *map(str, position))
                            time.sleep(2)
                    current = [n for n in ET.fromstring(common.dump_ui()).iter('node')
                               if n.get('bounds') == bounds and n.get('class', '').endswith('Switch')]
                    report['autocorrect'] = ('disabled via Gboard settings' if current
                                             and current[0].get('checked') == 'false' else 'not confirmed')
                    common.run('adb', 'shell', 'input', 'keyevent', '4')
                    time.sleep(2)
                    return
                group = parents.get(group)
                if group is None:
                    break
        swipe_down_page()
    report['autocorrect'] = 'auto-correction switch not located'
    report['corrections_final_labels'] = labels()
    common.run('adb', 'shell', 'input', 'keyevent', '4')
    time.sleep(2)


def enable_via_settings(report: dict) -> bool:
    command = common.run('adb', 'shell', 'am', 'start', '-n',
        f'{PACKAGE}/com.google.android.apps.inputmethod.latin.preference.SettingsActivity')
    report['settings_launch'] = command[:300]
    if 'Error:' in command:
        return False
    time.sleep(6)
    report['settings_initial_labels'] = labels()
    disable_autocorrect(report)
    report['patches_entry_found'] = find_and_tap('Patches')
    if not report['patches_entry_found']:
        report['settings_final_labels'] = labels()
        return False
    report['patches_labels'] = labels()
    return enable_on_patches_page(report, 'native Gboard settings')


def enable_on_patches_page(report: dict, route: str) -> bool:
    report['khmerlish_entry_found'] = find_and_tap('Khmerlish')
    if not report['khmerlish_entry_found']:
        report['patches_final_labels'] = labels()
        return False
    report['settings_entry'] = f'visible via {route} in test fixture'
    xml = common.dump_ui()
    switches = [n for n in ET.fromstring(xml).iter('node') if n.get('class', '').endswith('Switch')]
    if not switches or switches[0].get('checked') != 'false':
        return False
    report['settings_default_off'] = 'passed'
    position = common.center(switches[0].get('bounds', ''))
    if not position:
        return False
    common.run('adb', 'shell', 'input', 'tap', *map(str, position))
    time.sleep(2)
    switches = [n for n in ET.fromstring(common.dump_ui()).iter('node') if n.get('class', '').endswith('Switch')]
    if switches and switches[0].get('checked') == 'true':
        report['settings_toggle'] = 'passed'
        return True
    return False


def enable_via_test_launcher(report: dict) -> bool:
    command = ['adb', 'shell', 'am', 'instrument', '-w', '-r', '-e', 'open_settings', 'true',
               '-e', 'hold_ms', '45000', f'{TARGET_INSPECTOR_PACKAGE}/{TARGET_INSPECTOR}']
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    enabled = False
    try:
        time.sleep(5)
        report['direct_patches_labels'] = labels()
        enabled = enable_on_patches_page(report, 'same-signature test launcher')
    finally:
        try:
            output, _ = process.communicate(timeout=65)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate()
        match = re.search(r'^INSTRUMENTATION_RESULT: diagnostic=([A-Za-z0-9+/=]+)$', output, re.MULTILINE)
        if match:
            report['target_diagnostic_open_settings'] = json.loads(base64.b64decode(match.group(1)).decode('utf-8'))
    return enabled


def enable_via_root(tmp: Path, report: dict) -> bool:
    """Fallback for environments where UI automation cannot reach the page."""
    try:
        common.run('adb', 'root', timeout=30)
        common.run('adb', 'wait-for-device', timeout=60)
        if common.run('adb', 'shell', 'id', '-u') != '0':
            return False
        common.run('adb', 'shell', 'am', 'force-stop', PACKAGE)
        data = f'/data/user/0/{PACKAGE}'
        uid = common.run('adb', 'shell', 'stat', '-c', '%u', data)
        if not uid.isdecimal():
            return False
        prefs = data + '/shared_prefs/gboard_patches_settings.xml'
        result = subprocess.run(['adb', 'shell', 'cat', prefs], capture_output=True, text=True, check=False)
        root = ET.fromstring(result.stdout) if result.returncode == 0 and result.stdout.strip() else ET.Element('map')
        for child in list(root):
            if child.get('name') == PREF_KEY:
                root.remove(child)
        ET.SubElement(root, 'boolean', {'name': PREF_KEY, 'value': 'true'})
        local = tmp / 'prefs.xml'
        ET.ElementTree(root).write(local, encoding='utf-8', xml_declaration=True)
        common.run('adb', 'push', str(local), '/data/local/tmp/khmer-smoke-prefs.xml')
        common.run('adb', 'shell', 'mkdir', '-p', data + '/shared_prefs')
        common.run('adb', 'shell', 'cp', '/data/local/tmp/khmer-smoke-prefs.xml', prefs)
        common.run('adb', 'shell', 'chown', f'{uid}:{uid}', data + '/shared_prefs', prefs)
        common.run('adb', 'shell', 'chmod', '660', prefs)
        common.run('adb', 'shell', 'restorecon', '-R', data + '/shared_prefs')
        report['settings_toggle'] = 'set by root in disposable emulator; settings UI not confirmed'
        return True
    except (RuntimeError, OSError, subprocess.TimeoutExpired, ET.ParseError):
        return False


def keyboard_keys() -> dict[str, tuple[int, int]]:
    """Use actual Gboard accessibility bounds; never assume key coordinates."""
    nodes = list(common.flatten_window_nodes(common.inspect_ime_windows()))
    keys = {}
    for node in nodes:
        position = common.center(str(node.get('bounds', '')))
        if not position:
            continue
        text = str(node.get('text', '')).strip().lower()
        desc = str(node.get('description', '')).strip().lower()
        for label in (text, desc):
            if re.fullmatch('[a-z]', label):
                keys.setdefault(label, position)
            if label == 'space' or label.startswith('space,') or label.startswith('space bar'):
                keys.setdefault(' ', position)
    return keys


def enter(text: str, keys: dict[str, tuple[int, int]] | None) -> None:
    for word in text.lower().split(' '):
        if keys is None:
            common.run('adb', 'shell', 'input', 'text', word)
            common.run('adb', 'shell', 'input', 'keyevent', '62')
        else:
            for letter in word + ' ':
                common.run('adb', 'shell', 'input', 'tap', *map(str, keys[letter]))
                time.sleep(0.12)
        time.sleep(2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixture_apk', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('--fixture-keystore', type=Path, required=True)
    args = parser.parse_args()
    report = {
        'environment': 'disposable Android emulator, synthetic text only',
        'fixture': 're-signed hybrid of third-party prepatched Gboard and the actual MPP output; not stock',
        'fixture_install': 'not run', 'ime_selected': 'not run',
        'settings_entry': 'not tested', 'settings_default_off': 'not tested', 'settings_toggle': 'not tested',
        'actual_gboard_typing': 'not tested',
    }
    failed = False
    try:
        with tempfile.TemporaryDirectory(prefix='gboard-khmer-smoke-') as directory:
            tmp = Path(directory)
            report['android_api'] = common.run('adb', 'shell', 'getprop', 'ro.build.version.sdk')
            install_and_select(args.fixture_apk, report)
            build_probes(tmp, args.fixture_keystore)
            report['target_diagnostic_before'] = target_diagnostic()
            common.run('adb', 'logcat', '-c')
            open_editor()
            time.sleep(5)
            visible = common.ime_visibility_flags(common.run('adb', 'shell', 'dumpsys', 'input_method', timeout=30))
            report['ime_visibility_flags'] = visible
            if not (visible.get('mInputShown') or visible.get('isInputViewShown')):
                raise RuntimeError('Gboard keyboard did not become visible')
            report['ime_visible'] = 'passed'
            # Before the toggle, synthetic English remains untouched.
            enter('nv', None)
            report['default_off_example'] = 'passed' if editor_text().rstrip().lower() == 'nv' else 'failed'
            enabled = enable_via_settings(report)
            if not enabled:
                enabled = enable_via_test_launcher(report)
            report['target_diagnostic_after_settings'] = target_diagnostic()
            if not enabled or not report['target_diagnostic_after_settings'].get('runtime_enabled'):
                report['target_diagnostic_programmatic_enable'] = target_diagnostic(enable=True)
                if not report['target_diagnostic_programmatic_enable'].get('runtime_enabled'):
                    if not enable_via_root(tmp, report):
                        raise RuntimeError('Could not enable Khmerlish in the disposable emulator')
                    report['target_diagnostic_after_root'] = target_diagnostic()
                    if not report['target_diagnostic_after_root'].get('runtime_enabled'):
                        raise RuntimeError('The Gboard runtime did not observe its enabled setting')
                else:
                    report['settings_toggle'] = 'set using same-signature test instrumentation; UI not confirmed'
            open_editor()
            time.sleep(5)
            examples = {'nv na': 'នៅណា', 'kampuchea': 'កម្ពុជា', 'kampu': 'កម្ពុជា',
                        'nak na': 'អ្នកណា', 'srey sart': 'ស្រីស្អាត', 'nik o': 'នឹកអូន'}
            try:
                keys = keyboard_keys()
            except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired):
                keys = {}
            required = set(''.join(examples.keys()))
            if not required.issubset(keys):
                keys = None
                report['input_method'] = 'hardware key events to a focused editor while Gboard IME is active'
            else:
                report['input_method'] = 'taps on the actual Gboard soft-key accessibility bounds'
            results = {}
            for source, expected in examples.items():
                open_editor()
                enter(source, keys)
                actual = editor_text().rstrip()
                results[source] = {'expected': expected, 'actual': actual, 'passed': actual == expected}
            report['examples'] = results
            all_pass = all(x['passed'] for x in results.values())
            report['actual_gboard_typing'] = 'passed' if all_pass else 'failed'
            crashes = common.gboard_crash_types(common.run('adb', 'logcat', '-d', '-s', 'AndroidRuntime:E', '*:S'))
            if crashes:
                report['gboard_fatal_exception_types'] = crashes
            failed = (not all_pass or report['default_off_example'] != 'passed' or bool(crashes)
                      or report['settings_default_off'] != 'passed' or report['settings_toggle'] != 'passed')
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired, ET.ParseError) as error:
        report['error'] = f'{type(error).__name__}: {error}'
        failed = True
    finally:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
