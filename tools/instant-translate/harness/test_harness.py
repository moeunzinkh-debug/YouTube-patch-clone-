#!/usr/bin/env python3
"""Exercise the settings dialog in a CI-only host using one synthetic API key.

This does not modify, launch or bypass integrity checks in the original app; no
real API key or provider request is used. Only booleans are written to the report.
"""
import json
import os
import re
import subprocess
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from probe_runtime import adb, dump

PACKAGE = 'app.morphe.instanttranslate.harness'
ACTIVITY = 'app.morphe.extension.instanttranslate.HarnessActivity'
DIR = Path(os.environ['RUNNER_TEMP']) / 'instant-harness'
REPORT = DIR / 'settings-harness.json'
FIXTURE = b'fixture-key-2026'


def wait_nodes(predicate, description, seconds=35):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        nodes = dump()
        result = next((n for n in nodes if predicate(n)), None)
        if result:
            return nodes, result
        time.sleep(1)
    raise RuntimeError('UI element not found: ' + description)


def tap(node):
    bounds = node.get('bounds', '')
    if not re.fullmatch(r'\[\d+,\d+\]\[\d+,\d+\]', bounds): raise RuntimeError('Invalid UI bounds')
    a, b, c, d = map(int, re.findall(r'\d+', bounds))
    adb('shell', 'input', 'tap', str((a+c)//2), str((b+d)//2))
    time.sleep(1)


def text(value, partial=False):
    _, node = wait_nodes(lambda n: (value.casefold() in (n.get('text') or '').casefold()) if partial else
                        (n.get('text') or '').casefold() == value.casefold(), value)
    return node


def click(value, partial=False): tap(text(value, partial))


def restart():
    adb('shell', 'am', 'force-stop', PACKAGE, check=False)
    adb('shell', 'am', 'start', '-n', f'{PACKAGE}/{ACTIVITY}')
    text('Settings Patch >')


def private_file(path):
    return subprocess.run(['adb', 'exec-out', 'run-as', PACKAGE, 'cat', path], capture_output=True, timeout=30)


def main():
    result = {'scope': 'CI-only settings harness; synthetic key and mock provider only',
              'original_apk_modified': False, 'real_api_called': False}
    stage = 'install'
    try:
        install = adb('install', '-r', '-t', '--no-incremental', str(DIR / 'harness.apk'), timeout=240)
        if 'Success' not in install.splitlines(): raise RuntimeError('Harness install failed')
        restart()
        stage = 'open settings and dropdown'
        click('Settings Patch >')
        _, spinner = wait_nodes(lambda n: n.get('class') == 'android.widget.Spinner', 'provider dropdown')
        tap(spinner)
        click('Sea-Lion Translate Ai')
        result['provider_in_dropdown'] = True
        nodes = dump()
        labels = [(n.get('text') or '') for n in nodes]
        result['default_name_visible'] = any(x == 'Sea-Lion Translate Ai' for x in labels)
        result['default_url_visible'] = any(x == 'https://api.sea-lion.ai/v1/' for x in labels)
        result['default_model_visible'] = any(x == 'aisingapore/Gemma-SEA-LION-v4-27B-IT' for x in labels)
        # The password field can be below the fold on a small emulator.
        stage = 'enter synthetic key'
        for _ in range(4):
            nodes = dump()
            key = next((n for n in nodes if n.get('class') == 'android.widget.EditText' and
                        ('api key' in (n.get('text') or '').lower() or 'api key' in (n.get('hint') or '').lower())), None)
            if key: break
            adb('shell', 'input', 'swipe', '160', '485', '160', '200', '400'); time.sleep(1)
        else: raise RuntimeError('Key input not found')
        tap(key)
        adb('shell', 'input', 'text', FIXTURE.decode('ascii'))
        adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
        stage = 'save and consent'
        click('Save')
        click('I understand')
        text('Settings Patch >')
        result['saved'] = True
        stage = 'verify encrypted storage and restart'
        prefs = private_file('shared_prefs/morphe_instant_translate_settings.xml')
        encrypted = private_file('no_backup/morphe-instant-sealion-key.v1')
        if prefs.returncode or encrypted.returncode: raise RuntimeError('Private settings or encrypted file not found')
        result['key_not_plaintext_in_prefs_or_file'] = FIXTURE not in prefs.stdout and FIXTURE not in encrypted.stdout and len(encrypted.stdout) > 30
        if not result['key_not_plaintext_in_prefs_or_file']: raise RuntimeError('Key is present in plaintext')
        restart()
        click('Verify saved fixture')
        text('SEA-LION CONFIG AND ROUTING OK')
        result['persisted_and_routed_to_selected_mock'] = True
        stage = 'reopen and clear key'
        click('Settings Patch >')
        text('Sea-Lion Translate Ai')
        result['provider_persisted'] = True
        click('Clear key')
        click('Clear')
        # adb exec-out does not reliably propagate the shell command's status;
        # inspect the directory listing rather than relying on cat's exit code.
        remaining = adb('shell', 'run-as', PACKAGE, 'ls', 'no_backup', check=False)
        result['key_file_deleted'] = 'morphe-instant-sealion-key.v1' not in remaining
        if not result['key_file_deleted']: raise RuntimeError('Encrypted key was not deleted')
        result['cleared_provider_original'] = b'original' in private_file('shared_prefs/morphe_instant_translate_settings.xml').stdout
        if not result['cleared_provider_original']: raise RuntimeError('Clear did not disable SEA-LION')
    except Exception as error:
        result['failure_stage'] = stage
        result['failure_type'] = type(error).__name__
        try:
            # Never capture the content of EditText fields (including the fixture key).
            result['visible_labels'] = [(n.get('text') or '')[:80] for n in dump()
                                        if n.get('class') != 'android.widget.EditText' and n.get('text')][:30]
        except Exception:
            pass
        raise
    finally:
        REPORT.write_text(json.dumps(result, indent=2) + '\n')
    if not all(result.get(k) for k in ('provider_in_dropdown','default_name_visible','default_url_visible',
                                       'default_model_visible','saved','key_not_plaintext_in_prefs_or_file',
                                       'persisted_and_routed_to_selected_mock','provider_persisted',
                                       'key_file_deleted','cleared_provider_original')):
        raise RuntimeError('Settings harness fixture incomplete')
    print('Settings harness fixture passed; no real key, endpoint or patched APK used')


if __name__ == '__main__': main()
