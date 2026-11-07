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


def run_synthetic(*command: str, timeout: int = 60) -> str:
    """Like the shared runner, but report the failing command stage precisely."""
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=timeout, check=False)
    if result.returncode:
        if Path(command[0]).name == 'adb':
            limit = 4 if tuple(command[1:4]) == ('shell', 'input', 'text') else 5
            stage = ' '.join(command[:limit])
        else:
            stage = Path(command[0]).name
        diagnostic = re.search(r'(?:INSTALL_FAILED_[A-Z0-9_]+|device offline|device not found|'
                               r'no devices/emulators found|(?:[A-Za-z_][\\w$]*\\.)*[A-Za-z_][\\w$]*(?:Exception|Error))',
                               result.stdout, re.IGNORECASE)
        detail = f' [{diagnostic.group(0)}]' if diagnostic else ''
        raise RuntimeError(f'{stage} failed (exit {result.returncode}){detail}')
    return result.stdout.strip()


# The shared UI helpers call their module's run(), so they inherit these
# sanitized diagnostics as well. The emulator contains only synthetic data.
common.run = run_synthetic


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
        str(ROOT / 'tools/gboard-khmer/AndroidSyntheticUi.java'),
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
            <instrumentation android:name="dev.arena.khmerprobe.AndroidSyntheticUi" android:targetPackage="{INSPECTOR_PACKAGE}" />
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


def target_diagnostic(enable: bool = False, open_settings: bool = False, personal: bool = False) -> dict:
    command = ['adb', 'shell', 'am', 'instrument', '-w', '-r']
    if enable:
        command.extend(['-e', 'enable', 'true'])
    if open_settings:
        command.extend(['-e', 'open_settings', 'true'])
    if personal:
        command.extend(['-e', 'personal', 'true'])
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


def set_synthetic_field(description: str, text: str) -> None:
    # adb shell drops an empty argument, so use an explicit sentinel for an
    # empty field instead of passing an empty base64 string to instrumentation.
    encode = lambda value: base64.b64encode(value.encode('utf-8')).decode('ascii') if value else '__empty__'
    output = common.run('adb', 'shell', 'am', 'instrument', '-w', '-r',
                        '-e', 'description', encode(description), '-e', 'value', encode(text),
                        f'{INSPECTOR_PACKAGE}/dev.arena.khmerprobe.AndroidSyntheticUi', timeout=45)
    if 'INSTRUMENTATION_RESULT: set=true' not in output:
        raise RuntimeError('Could not set the synthetic field: ' + description)
    time.sleep(1)


def click_synthetic_document(filename: str) -> bool:
    encoded = base64.b64encode(filename.encode('utf-8')).decode('ascii')
    output = common.run('adb', 'shell', 'am', 'instrument', '-w', '-r',
                        '-e', 'action', 'click_document', '-e', 'description', 'dW51c2Vk',
                        '-e', 'value', encoded,
                        f'{INSPECTOR_PACKAGE}/dev.arena.khmerprobe.AndroidSyntheticUi', timeout=45)
    return 'INSTRUMENTATION_RESULT: clicked=true' in output


def wait_for_text(text: str, seconds: int = 15) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if any(text.lower() in label.lower() for label in labels()):
            return True
        time.sleep(1)
    return False


def wait_for_exact_text(text: str, seconds: int = 15) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if text in labels():
            return True
        time.sleep(1)
    return False


def require_tap(label: str, scroll: bool = False) -> None:
    if not find_and_tap(label, scroll=scroll):
        raise RuntimeError('Synthetic UI action not found: ' + label)


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
            # Send individually, like real typing. A single `input text word`
            # burst can make every selection callback stale before the IME has
            # observed the word, which correctly causes the safety guard to skip.
            for letter in word:
                common.run('adb', 'shell', 'input', 'text', letter)
                time.sleep(.18)
            time.sleep(.5)
            common.run('adb', 'shell', 'input', 'keyevent', '62')
        else:
            for letter in word + ' ':
                common.run('adb', 'shell', 'input', 'tap', *map(str, keys[letter]))
                time.sleep(0.12)
        time.sleep(2)



def ime_labels(windows: list) -> list[str]:
    # Only disposable, synthetic emulator text is present in this test.
    labels = []
    for node in common.flatten_window_nodes(windows):
        label = str(node.get('description', '') or node.get('text', '')).strip()
        if label and label not in labels:
            labels.append(label[:100])
    return labels[:100]


def tap_panel_icon(panel_report: dict) -> bool:
    windows = common.inspect_ime_windows()
    panel_report.setdefault('initial_toolbar_labels', ime_labels(windows))
    panel_report.setdefault('native_layout_paths', keyboard_layout_paths(windows))
    panel_report.setdefault('initial_unlabelled_clickable_nodes', [
        {key: str(node.get(key, ''))[:120] for key in ('class', 'id', 'bounds')}
        for node in common.flatten_window_nodes(windows)
        if node.get('clickable') and not node.get('description') and not node.get('text')
    ][:30])
    direct = any('khmerlish' in (str(n.get('description', '')) + ' ' + str(n.get('text', ''))).lower()
                 for n in common.flatten_window_nodes(windows))
    panel_report.setdefault('visible_in_toolbar', 'passed' if direct else 'not initially visible')
    if not direct and common.tap_ime_label(windows, 'open features menu'):
        time.sleep(2)
        windows = common.inspect_ime_windows()
    if not common.tap_ime_label(windows, 'khmerlish'):
        panel_report['labels_before_panel'] = ime_labels(windows)
        return False
    time.sleep(2)
    return True


def keyboard_layout_paths(windows: list) -> dict[str, list[dict[str, str]]]:
    """Record only view classes, IDs and bounds for known synthetic-test nodes."""
    wanted = {
        'khmerlish offline panel': 'panel', 'khmerlish key a': 'panel_a',
        'khmerlish key n': 'panel_n', 'khmerlish key space': 'panel_space',
        'a': 'native_a', 'n': 'native_n', 'space': 'native_space',
    }
    result: dict[str, list[dict[str, str]]] = {}

    def visit(node: dict, ancestors: list[dict[str, str]]) -> None:
        identity = {key: str(node.get(key, ''))[:150] for key in ('class', 'id', 'bounds')}
        path = ancestors + [identity]
        for value in (node.get('description', ''), node.get('text', '')):
            name = wanted.get(str(value).strip().lower())
            if name and name not in result:
                result[name] = path
        for child in node.get('children', []):
            if isinstance(child, dict):
                visit(child, path)

    for window in windows:
        if isinstance(window, dict):
            visit(window, [])
    return result


def panel_key_positions(windows: list) -> dict[str, tuple[int, int]]:
    positions = {}
    for node in common.flatten_window_nodes(windows):
        label = str(node.get('description', '')).strip().lower()
        if label.startswith('khmerlish key '):
            position = common.center(str(node.get('bounds', '')))
            if position:
                positions[label.removeprefix('khmerlish key ')] = position
        elif label in ('khmerlish backspace', 'khmerlish shift', 'done khmerlish'):
            position = common.center(str(node.get('bounds', '')))
            if position:
                positions[label] = position
    return positions


def panel_press(text: str) -> None:
    for character in text:
        name = 'space' if character == ' ' else character.lower()
        # Android may resize/reposition the IME when the editor changes. Never
        # reuse stale coordinates for an actual user-visible soft key.
        current = panel_key_positions(common.inspect_ime_windows())
        if character.isupper():
            if 'khmerlish shift' not in current:
                raise RuntimeError('Synthetic Khmerlish shift is missing')
            common.run('adb', 'shell', 'input', 'tap', *map(str, current['khmerlish shift']))
            current = panel_key_positions(common.inspect_ime_windows())
        if name not in current:
            raise RuntimeError('Synthetic Khmerlish key is missing: ' + name)
        common.run('adb', 'shell', 'input', 'tap', *map(str, current[name]))
        time.sleep(.25)


def rect(bounds: str) -> tuple[int, int, int, int] | None:
    values = re.fullmatch(r'\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]', bounds)
    return tuple(map(int, values.groups())) if values else None


def panel_within_native_keyboard(native_paths: dict, panel_paths: dict) -> bool:
    holder = next((item for item in native_paths.get('native_a', [])
                   if item.get('id', '').endswith(':id/keyboard_holder')), None)
    path = panel_paths.get('panel', [])
    native = rect(holder.get('bounds', '')) if holder else None
    panel = rect(path[-1].get('bounds', '')) if path else None
    if not native or not panel:
        return False
    nl, nt, nr, nb = native
    pl, pt, pr, pb = panel
    return nl <= pl < pr <= nr and nt <= pt < pb <= nb


def panel_snapshot() -> dict:
    windows = common.inspect_ime_windows()
    nodes = list(common.flatten_window_nodes(windows))
    active = any(str(node.get('description', '')).lower() == 'khmerlish offline panel' for node in nodes)
    lower = next((str(node.get('text', '')) for node in nodes
                  if str(node.get('description', '')).lower() == 'khmerlish input'), '')
    positions = panel_key_positions(windows)
    tracked = {name: positions[name] for name in ('a', 'n', 'v', 'space', 'khmerlish backspace', 'done khmerlish')
               if name in positions}
    return {'panel_visible': active, 'lower_input': lower, 'host_output': editor_text(), 'key_positions': tracked}


def panel_smoke(report: dict) -> bool:
    """Tap the real toolbar, then verify live host output while the emulator is offline."""
    result = report['toolbar_panel'] = {'status': 'not tested'}
    offline = False
    try:
        open_editor()
        if not tap_panel_icon(result):
            raise RuntimeError('Khmerlish toolbar access point was not found')
        windows = common.inspect_ime_windows()
        result['labels_after_tap'] = ime_labels(windows)
        result['panel_layout_paths'] = keyboard_layout_paths(windows)
        result['screen_size'] = common.run('adb', 'shell', 'wm', 'size')
        if not any('khmerlish offline panel' in str(n.get('description', '')).lower()
                   for n in common.flatten_window_nodes(windows)):
            raise RuntimeError('Khmerlish panel did not open')
        contained = panel_within_native_keyboard(result.get('native_layout_paths', {}), result['panel_layout_paths'])
        result['panel_within_native_keyboard'] = 'passed' if contained else 'failed'
        if not contained:
            raise RuntimeError('Panel must stay within the existing keyboard area')
        keys = panel_key_positions(windows)
        result['key_count'] = len(keys)
        if not set('nvakmpuchesrtoyl').union({'space', 'khmerlish backspace', 'done khmerlish'}).issubset(keys):
            raise RuntimeError('Khmerlish panel keys were not accessible')
        common.run('adb', 'shell', 'cmd', 'connectivity', 'airplane-mode', 'enable')
        offline = common.run('adb', 'shell', 'settings', 'get', 'global', 'airplane_mode_on') == '1'
        result['airplane_mode'] = 'enabled' if offline else 'not confirmed'
        if not offline:
            raise RuntimeError('Could not confirm airplane mode in disposable emulator')
        snapshots = result['snapshots'] = {}
        panel_press('n')
        snapshots['n'] = panel_snapshot()
        if not snapshots['n']['panel_visible']:
            raise RuntimeError('Panel closed after the first character')
        panel_press('v')
        snapshots['nv'] = panel_snapshot()
        if not snapshots['nv']['panel_visible']:
            raise RuntimeError('Panel closed after the second character')
        after_nv = snapshots['nv']['host_output']
        panel_press(' na')
        snapshots['nv na'] = panel_snapshot()
        if not snapshots['nv na']['panel_visible']:
            raise RuntimeError('Panel closed while entering the phrase')
        after_phrase = snapshots['nv na']['host_output']
        keys = panel_key_positions(common.inspect_ime_windows())
        common.run('adb', 'shell', 'input', 'tap', *map(str, keys['khmerlish backspace']))
        time.sleep(1)
        snapshots['after backspace'] = panel_snapshot()
        after_delete = snapshots['after backspace']['host_output']
        panel_press('a')
        snapshots['after retype'] = panel_snapshot()
        after_restore = snapshots['after retype']['host_output']
        result['live_steps'] = {
            'nv': after_nv, 'nv na': after_phrase,
            'after_backspace': after_delete, 'after_retype': after_restore,
        }
        keys = panel_key_positions(common.inspect_ime_windows())
        common.run('adb', 'shell', 'input', 'tap', *map(str, keys['done khmerlish']))
        time.sleep(2)
        after_close = editor_text()
        result['close_commits'] = 'passed' if after_close == 'នៅណា' else 'failed'
        if not tap_panel_icon(result):
            raise RuntimeError('Khmerlish icon could not reopen the panel')
        panel_press('kampu')
        after_reopen = editor_text()
        result['reopen_output'] = after_reopen
        result['reopen'] = 'passed' if after_reopen == 'នៅណាកម្ពុជា' else 'failed'
        new_keys = panel_key_positions(common.inspect_ime_windows())
        common.run('adb', 'shell', 'input', 'tap', *map(str, new_keys['done khmerlish']))
        examples = {'nv na': 'នៅណា', 'Kampuchea': 'កម្ពុជា', 'kampuchea': 'កម្ពុជា',
                    'kampu': 'កម្ពុជា', 'nak na': 'អ្នកណា', 'srey sart': 'ស្រីស្អាត', 'Nik o': 'នឹកអូន'}
        tested = {}
        for source, expected in examples.items():
            open_editor()
            if not tap_panel_icon(result):
                raise RuntimeError('Khmerlish panel failed to reopen for an example')
            panel_press(source)
            snapshot = panel_snapshot()
            actual = snapshot['host_output']
            tested[source] = {'expected': expected, 'actual': actual, 'lower_input': snapshot['lower_input'],
                              'passed': snapshot['panel_visible'] and snapshot['lower_input'] == source and expected == actual}
            example_keys = panel_key_positions(common.inspect_ime_windows())
            common.run('adb', 'shell', 'input', 'tap', *map(str, example_keys['done khmerlish']))
        result['examples'] = tested
        passed = (result['visible_in_toolbar'] == 'passed' and after_nv == 'នៅ'
                  and after_phrase == 'នៅណា' and after_delete == 'នៅ n'
                  and after_restore == 'នៅណា' and result['close_commits'] == 'passed'
                  and result['reopen'] == 'passed' and all(item['passed'] for item in tested.values()))
        result['status'] = 'passed' if passed else 'failed'
        return passed
    except (RuntimeError, ValueError, KeyError, OSError, subprocess.TimeoutExpired, ET.ParseError) as error:
        result['status'] = 'failed'
        result['error'] = f'{type(error).__name__}: {error}'
        try:
            result['labels_on_failure'] = ime_labels(common.inspect_ime_windows())
        except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired):
            pass
        return False
    finally:
        try:
            log = common.run('adb', 'logcat', '-d', '-s', 'GboardKhmerlish:D', '*:S', timeout=30)
            # The extension emits fixed stage names and exception types only;
            # never save arbitrary log text or text entered by the test.
            result['toolbar_debug_stages'] = re.findall(
                r'GboardKhmerlish\s*:\s*((?:catalog|register|state)_[a-z_0-9]+(?::[A-Za-z]+)?)', log)[-30:]
        except (RuntimeError, OSError, subprocess.TimeoutExpired):
            pass
        if offline:
            try:
                common.run('adb', 'shell', 'cmd', 'connectivity', 'airplane-mode', 'disable')
            except (RuntimeError, OSError, subprocess.TimeoutExpired):
                pass


def open_dictionary() -> None:
    command = common.run('adb', 'shell', 'am', 'start', '-n',
                         f'{PACKAGE}/com.google.android.apps.inputmethod.latin.preference.SettingsActivity')
    if 'Error:' in command:
        raise RuntimeError('Native Gboard settings could not be launched')
    time.sleep(5)
    # Android can bring the existing settings task to the foreground with the
    # dictionary activity still on top, instead of recreating the root screen.
    if any(label == 'Khmerlish Dictionary' for label in labels()):
        return
    require_tap('Patches', scroll=True)
    require_tap('Khmerlish', scroll=True)
    require_tap('Personal Dictionary & Documents', scroll=True)
    if not wait_for_text('Khmerlish Dictionary'):
        raise RuntimeError('Private dictionary screen did not open')


def personal_tab() -> None:
    require_tap('Personal dictionary')
    if not find_and_tap('Add personal word'):
        raise RuntimeError('Personal dictionary actions are unavailable')


def edit_synthetic_word(roman: str, khmer: str) -> None:
    set_synthetic_field('Personal Khmerlish spelling', roman)
    set_synthetic_field('Personal Khmer word', khmer)
    require_tap('Save')
    if not wait_for_text(roman + '  →  ' + khmer):
        raise RuntimeError('Saved synthetic entry did not appear')


def tap_word_edit_icon(roman: str, personal: bool = False) -> None:
    description = ('Edit personal word ' if personal else 'Edit word ') + roman
    for node in ET.fromstring(common.dump_ui()).iter('node'):
        if (node.get('class') == 'android.widget.ImageButton'
                and node.get('content-desc') == description and node.get('clickable') == 'true'):
            position = common.center(node.get('bounds', ''))
            if position:
                common.run('adb', 'shell', 'input', 'tap', *map(str, position))
                time.sleep(2)
                return
    raise RuntimeError('Visible edit icon not found: ' + description)


def tap_synthetic_filename(filename: str) -> bool:
    # Do not tap a thumbnail with content-desc "Preview the file ...": that
    # previews the file instead of choosing it. Use its exact text row.
    for node in ET.fromstring(common.dump_ui()).iter('node'):
        if node.get('text') == filename:
            position = common.center(node.get('bounds', ''))
            if position:
                common.run('adb', 'shell', 'input', 'tap', *map(str, position))
                time.sleep(2)
                return True
    return False


def select_document(filename: str) -> None:
    time.sleep(3)
    if tap_synthetic_filename(filename):
        return
    # DocumentsUI may start in Recents. Open its navigation drawer and choose
    # the Downloads root, which contains only files created by this smoke test.
    if not find_and_tap('Downloads'):
        for nav in ('Show roots', 'Open navigation drawer', 'Browse', 'Show navigation'):
            if find_and_tap(nav):
                break
        require_tap('Downloads')
    if not tap_synthetic_filename(filename):
        raise RuntimeError('Synthetic file is not visible in Downloads')


def import_document(filename: str, replace: bool | None = False) -> None:
    require_tap('Import dictionary file')
    require_tap('Choose file')
    select_document(filename)
    if replace is None:
        # Invalid input is rejected before the confirmation or any DB writes.
        for attempt in range(3):
            if wait_for_text('Khmerlish Dictionary', seconds=5):
                break
            if not click_synthetic_document(filename) and not tap_synthetic_filename(filename):
                raise RuntimeError('Invalid document was not returned by the picker')
        else:
            raise RuntimeError('Invalid synthetic document did not open')
        time.sleep(3)
        if any('Keep existing' in value for value in labels()):
            raise RuntimeError('Invalid document was offered for import')
        return
    # DocumentsUI on some images selects an item on the first tap and opens it
    # on the next; retry only while our exact synthetic filename remains visible.
    for attempt in range(3):
        if wait_for_text('Keep existing', seconds=5):
            break
        if not click_synthetic_document(filename) and not tap_synthetic_filename(filename):
            raise RuntimeError('Import preview did not appear')
    else:
        raise RuntimeError('Import preview did not appear after opening the synthetic file')
    require_tap('Replace' if replace else 'Keep existing')
    time.sleep(3)


def dictionary_smoke(tmp: Path, report: dict) -> bool:
    result = report['personal_dictionary'] = {'status': 'not tested'}
    try:
        # Synthetic UTF-8 documents are created only inside this disposable emulator.
        valid = tmp / 'khmerlish-smoke-valid.csv'
        valid.write_text('khmerlish,khmer\nnv,កម្ពុជា\nzztest,សួស្តី\nimported multi,ឃ្លានាំចូល\n', encoding='utf-8')
        invalid = tmp / 'khmerlish-smoke-invalid.csv'
        invalid.write_text('khmerlish,khmer\nnv,ផ្សេង\ninvalid,English\n', encoding='utf-8')
        for path in (valid, invalid):
            common.run('adb', 'push', str(path), '/sdcard/Download/' + path.name)

        open_dictionary()
        set_synthetic_field('Search Khmerlish or Khmer', 'srey')
        if not wait_for_text('srey  →  ស្រី'):
            raise RuntimeError('Built-in searchable word guide returned the wrong result')
        result['search_bundled'] = 'passed'
        tap_word_edit_icon('srey')
        set_synthetic_field('Personal Khmer word', 'ស្រីសាកល្បង')
        require_tap('Save')
        if not wait_for_text('srey  →  ស្រីសាកល្បង'):
            raise RuntimeError('Editing a bundled word did not create a personal override')
        result['bundled_edit_icon'] = 'passed'
        open_editor()
        time.sleep(4)
        enter('srey', None)
        if editor_text().rstrip() != 'ស្រីសាកល្បង':
            raise RuntimeError('Edited bundled word was not used by automatic typing')
        result['bundled_edit_conversion'] = 'passed'
        open_dictionary()
        require_tap('Word guide')
        set_synthetic_field('Search Khmerlish or Khmer', 'srey')
        if not wait_for_text('srey  →  ស្រីសាកល្បង'):
            raise RuntimeError('Edited bundled word did not persist')
        tap_word_edit_icon('srey', personal=True)
        require_tap('Delete')
        require_tap('Delete')
        if not wait_for_exact_text('srey  →  ស្រី'):
            raise RuntimeError('Deleting the override did not restore the bundled word')
        result['bundled_override_restore'] = 'passed'
        tap_word_edit_icon('srey')
        edit_synthetic_word('srey thmey', 'ស្រីថ្មី')
        set_synthetic_field('Search Khmerlish or Khmer', 'srey')
        if not (wait_for_exact_text('srey  →  ស្រី')
                and wait_for_text('srey thmey  →  ស្រីថ្មី')):
            raise RuntimeError('Changing a bundled spelling did not preserve the original and create a new pair')
        result['bundled_rename_copy'] = 'passed'
        tap_word_edit_icon('srey thmey', personal=True)
        require_tap('Delete')
        require_tap('Delete')
        if not wait_for_exact_text('srey  →  ស្រី'):
            raise RuntimeError('Original bundled spelling was not preserved after deleting the new pair')
        set_synthetic_field('Search Khmerlish or Khmer', '')
        personal_tab()  # Also opens the Add dialog.
        edit_synthetic_word('min dg del', 'ឃ្លាសាកល្បង')
        result['add_spaced_phrase'] = 'passed'
        tap_word_edit_icon('min dg del', personal=True)
        edit_synthetic_word('min dg del', 'ឃ្លាកែ')
        result['personal_edit_icon'] = 'passed'
        require_tap('Add personal word')
        edit_synthetic_word('nv', 'នាវា')
        result['add'] = 'passed'

        open_editor()
        time.sleep(4)
        enter('nv', None)
        if editor_text().rstrip() != 'នាវា':
            raise RuntimeError('Automatic typing ignored a personal override')
        result['automatic_override'] = 'passed'
        open_editor()
        time.sleep(3)
        panel_report = {}
        if not tap_panel_icon(panel_report):
            raise RuntimeError('Could not open the panel for a personal override')
        panel_press('nv')
        if editor_text() != 'នាវា':
            raise RuntimeError('Toolbar panel ignored a personal override')
        result['panel_override'] = 'passed'
        keys = panel_key_positions(common.inspect_ime_windows())
        common.run('adb', 'shell', 'input', 'tap', *map(str, keys['done khmerlish']))

        open_editor()
        time.sleep(4)
        enter('min dg del', None)
        if editor_text().rstrip() != 'ឃ្លាកែ':
            raise RuntimeError('Automatic typing ignored the spaced personal phrase')
        result['automatic_spaced_phrase'] = 'passed'
        open_editor()
        time.sleep(3)
        if not tap_panel_icon({}):
            raise RuntimeError('Could not open panel for a spaced personal phrase')
        panel_press('min dg del')
        if editor_text() != 'ឃ្លាកែ':
            raise RuntimeError('Toolbar panel ignored the spaced personal phrase')
        result['panel_spaced_phrase'] = 'passed'
        keys = panel_key_positions(common.inspect_ime_windows())
        common.run('adb', 'shell', 'input', 'tap', *map(str, keys['done khmerlish']))

        open_dictionary()
        require_tap('Personal dictionary')
        if not wait_for_text('nv  →  នាវា'):
            raise RuntimeError('Saved word did not persist when settings reopened')
        require_tap('Edit personal word nv')
        edit_synthetic_word('nv', 'នឹក')
        result['edit_and_persist'] = 'passed'
        import_document(valid.name)
        if (not wait_for_text('zztest  →  សួស្តី') or not wait_for_text('nv  →  នឹក')
                or not wait_for_text('imported multi  →  ឃ្លានាំចូល')):
            raise RuntimeError('Keep-existing import did not merge as previewed')
        result['import_keep_existing'] = 'passed'
        result['import_spaced_phrase'] = 'passed'
        import_document(valid.name, replace=True)
        if not wait_for_text('nv  →  កម្ពុជា'):
            raise RuntimeError('Explicit conflict replacement did not apply')
        result['import_replace_conflicts'] = 'passed'
        import_document(invalid.name, replace=None)
        if not wait_for_text('nv  →  កម្ពុជា') or not wait_for_text('zztest  →  សួស្តី'):
            raise RuntimeError('Invalid import changed the personal dictionary')
        result['invalid_import_atomic'] = 'passed'
        require_tap('Word guide')
        set_synthetic_field('Search Khmerlish or Khmer', 'zztest')
        if not wait_for_text('zztest  →  សួស្តី'):
            raise RuntimeError('Imported word was missing from the guide')
        result['search_personal'] = 'passed'
        set_synthetic_field('Search Khmerlish or Khmer', '')
        require_tap('Personal dictionary')

        require_tap('Export personal dictionary')
        time.sleep(3)
        if not find_and_tap('Downloads'):
            for nav in ('Show roots', 'Open navigation drawer', 'Browse', 'Show navigation'):
                if find_and_tap(nav):
                    break
            require_tap('Downloads')
        result['synthetic_save_dialog_labels'] = labels()
        require_tap('Save')
        time.sleep(4)
        # Some document providers append an extension or save in Documents
        # rather than Downloads; enumerate only our synthetic export name.
        candidates = []
        for directory in ('/sdcard/Download', '/sdcard/Documents'):
            found = subprocess.run(['adb', 'shell', 'find', directory, '-maxdepth', '3',
                                    '-type', 'f', '-name', 'khmerlish-personal*'],
                                   text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   timeout=30, check=False)
            candidates.extend(line.strip() for line in found.stdout.splitlines()
                              if '/khmerlish-personal' in line)
        result['synthetic_export_candidates'] = candidates
        if len(candidates) != 1:
            raise RuntimeError('The exported synthetic file was not found in device storage')
        exported = common.run('adb', 'shell', 'cat', candidates[0])
        if not all(row in exported for row in ('khmerlish\tkhmer', 'nv\tកម្ពុជា', 'zztest\tសួស្តី',
                                               'min dg del\tឃ្លាកែ', 'imported multi\tឃ្លានាំចូល')):
            raise RuntimeError('Exported UTF-8 TSV did not contain the synthetic entries')
        result['export'] = 'passed'

        require_tap('Edit personal word nv')
        require_tap('Delete')
        require_tap('Delete')
        if not wait_for_text('zztest  →  សួស្តី'):
            raise RuntimeError('Remaining word disappeared after delete')
        result['delete'] = 'passed'
        # Stop the target to prove the imported word survives a process restart.
        # Android can switch back to the preinstalled IME when a selected
        # package is force-stopped; explicitly restore the same test IME below.
        fixture_ime = common.run('adb', 'shell', 'settings', 'get', 'secure', 'default_input_method')
        if not fixture_ime.startswith(PACKAGE + '/'):
            raise RuntimeError('The test IME was not selected before restart')
        common.run('adb', 'shell', 'am', 'force-stop', PACKAGE)
        # Explicitly relaunch Gboard to clear Android's stopped-package state
        # before requesting its IME from the synthetic editor.
        common.run('adb', 'shell', 'am', 'start', '-n',
                   f'{PACKAGE}/com.google.android.apps.inputmethod.latin.preference.SettingsActivity')
        time.sleep(3)
        diagnostic = target_diagnostic(personal=True)
        result['after_restart_diagnostic'] = diagnostic
        if not (diagnostic.get('synthetic_import_persisted')
                and diagnostic.get('synthetic_override_deleted') and diagnostic.get('runtime_enabled')):
            raise RuntimeError('Personal entries or the enabled setting did not persist after restart')
        result['ime_after_force_stop'] = common.run(
                'adb', 'shell', 'settings', 'get', 'secure', 'default_input_method')
        common.run('adb', 'shell', 'ime', 'enable', fixture_ime)
        common.run('adb', 'shell', 'ime', 'set', fixture_ime)
        open_editor()
        time.sleep(6)
        result['restart_ime_component'] = common.run(
                'adb', 'shell', 'settings', 'get', 'secure', 'default_input_method')
        result['restart_keyboard_labels'] = ime_labels(common.inspect_ime_windows())
        if not result['restart_ime_component'].startswith(PACKAGE + '/'):
            raise RuntimeError('Android selected a different IME after force-stop')
        restarted_panel = {}
        if not tap_panel_icon(restarted_panel):
            raise RuntimeError('Could not open the Khmerlish panel after restarting Gboard')
        panel_press('zztest')
        if editor_text() != 'សួស្តី':
            raise RuntimeError('The restarted panel did not load the imported word')
        result['panel_after_restart'] = 'passed'
        keys = panel_key_positions(common.inspect_ime_windows())
        common.run('adb', 'shell', 'input', 'tap', *map(str, keys['done khmerlish']))
        open_editor()
        time.sleep(4)
        if not tap_panel_icon({}):
            raise RuntimeError('Could not reopen panel for persisted phrase')
        panel_press('min dg del')
        if editor_text() != 'ឃ្លាកែ':
            raise RuntimeError('Spaced personal phrase did not survive process restart')
        result['phrase_after_restart'] = 'passed'
        keys = panel_key_positions(common.inspect_ime_windows())
        common.run('adb', 'shell', 'input', 'tap', *map(str, keys['done khmerlish']))
        open_editor()
        time.sleep(4)
        keys = keyboard_keys()
        if not set('zztest ').issubset(keys):
            raise RuntimeError('Real Gboard keys were unavailable after restart')
        enter('zztest', keys)
        if editor_text().rstrip() != 'សួស្តី':
            raise RuntimeError('Automatic mode did not load the imported word after restart')
        open_editor()
        time.sleep(4)
        keys = keyboard_keys()
        if not set('nv ').issubset(keys):
            raise RuntimeError('Real Gboard keys were unavailable for delete fallback')
        enter('nv', keys)
        if editor_text().rstrip() != 'នៅ':
            raise RuntimeError('Deleting an override did not restore the built-in word')
        result['restart_and_delete_fallback'] = 'passed'
        result['status'] = 'passed'
        return True
    except (RuntimeError, ValueError, KeyError, OSError, subprocess.TimeoutExpired, ET.ParseError) as error:
        result['status'] = 'failed'
        result['error'] = f'{type(error).__name__}: {error}'
        try:
            result['synthetic_screen_labels_on_failure'] = labels()
            # Only synthetic filenames and file-picker controls are recorded;
            # do not capture arbitrary real user content or screenshots.
            result['synthetic_picker_nodes'] = [
                {key: node.get(key, '')[:150] for key in
                 ('text', 'content-desc', 'class', 'bounds', 'clickable', 'enabled', 'selected')}
                for node in ET.fromstring(common.dump_ui()).iter('node')
                if any(token in (node.get('text', '') + ' ' + node.get('content-desc', '')).lower()
                       for token in ('khmerlish-smoke-', 'downloads', 'open'))
            ][:25]
        except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired, ET.ParseError):
            pass
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixture_apk', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('--fixture-keystore', type=Path, required=True)
    parser.add_argument('--personal-only', action='store_true',
                        help='skip the long bundled-example regression while debugging dictionary UI')
    args = parser.parse_args()
    report = {
        'environment': 'disposable Android emulator, synthetic text only',
        'mode': 'personal-only diagnostic' if args.personal_only else 'complete smoke',
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
            report['phase'] = 'clear synthetic log and open editor'
            common.run('adb', 'shell', 'setprop', 'log.tag.GboardKhmerlish', 'DEBUG')
            common.run('adb', 'logcat', '-c')
            open_editor()
            report['phase'] = 'wait for Gboard IME'
            time.sleep(5)
            visible = common.ime_visibility_flags(common.run('adb', 'shell', 'dumpsys', 'input_method', timeout=30))
            report['ime_visibility_flags'] = visible
            if not (visible.get('mInputShown') or visible.get('isInputViewShown')):
                raise RuntimeError('Gboard keyboard did not become visible')
            report['ime_visible'] = 'passed'
            report['phase'] = 'verify feature is disabled by default'
            # Before the toggle, synthetic English remains untouched.
            enter('nv', None)
            report['default_off_example'] = 'passed' if editor_text().rstrip().lower() == 'nv' else 'failed'
            panel_passed = True
            if not args.personal_only:
                report['phase'] = 'test offline Khmerlish toolbar panel while automatic conversion is off'
                panel_passed = panel_smoke(report)
                if not panel_passed:
                    report['toolbar_diagnostic_after_panel'] = target_diagnostic()
                    raise RuntimeError('Khmerlish toolbar panel failed; see sanitized diagnostics')
            report['phase'] = 'navigate Gboard patch settings'
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
            all_pass = True
            if not args.personal_only:
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
                report['phase'] = 'type synthetic examples'
                for source, expected in examples.items():
                    open_editor()
                    enter(source, keys)
                    actual = editor_text().rstrip()
                    results[source] = {'expected': expected, 'actual': actual, 'passed': actual == expected}
                report['examples'] = results
                all_pass = all(x['passed'] for x in results.values())
                report['actual_gboard_typing'] = 'passed' if all_pass else 'failed'
            report['phase'] = 'exercise personal dictionary, guide and documents'
            personal_passed = dictionary_smoke(tmp, report)
            crashes = common.gboard_crash_types(common.run('adb', 'logcat', '-d', '-s', 'AndroidRuntime:E', '*:S'))
            if crashes:
                report['gboard_fatal_exception_types'] = crashes
            failed = (not panel_passed or not all_pass or not personal_passed
                      or report['default_off_example'] != 'passed' or bool(crashes)
                      or report['settings_default_off'] != 'passed' or report['settings_toggle'] != 'passed')
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired, ET.ParseError) as error:
        report['error'] = f'{type(error).__name__}: {error}'
        try:
            crashes = common.gboard_crash_types(common.run('adb', 'logcat', '-d', '-s', 'AndroidRuntime:E', '*:S'))
            if crashes:
                report['gboard_fatal_exception_types'] = crashes
        except (RuntimeError, OSError, subprocess.TimeoutExpired):
            pass
        failed = True
    finally:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
