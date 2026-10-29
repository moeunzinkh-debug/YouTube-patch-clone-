#!/usr/bin/env python3
"""Verify optional SimSimi quick-return hooks in actual Morphe-patched APKs."""
import gc
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

from androguard.core.apk import APK
from androguard.core.dex import DEX
from loguru import logger

logger.remove()
original, combined, quick_only, pull_only, report_path = map(Path, sys.argv[1:6])
CONTROLLER = 'Lcom/reactnativenavigation/viewcontrollers/bottomtabs/BottomTabsController;'
BAR = 'Lcom/aurelhubert/ahbottomnavigation/i;'
ACTIVITY = 'Lcom/ismaker/android/simsimi/MainActivity;'
QUICK = 'Lapp/morphe/extension/simsimi/QuickReturn;'
TAPS = 'Lapp/morphe/extension/simsimi/ChatTabDoubleTap;'
PULL = 'Lapp/morphe/extension/simsimi/PullRefresh;->onTouch('
HANDLERS = ('lambda$createClassicItems$5', 'lambda$createSmallItems$6')


def file_hash(archive, name):
    digest = hashlib.sha256()
    with archive.open(name) as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def inspect(path):
    apk = APK(str(path))
    if (apk.get_package(), apk.get_androidversion_name(), apk.get_androidversion_code()) != (
            'com.ismaker.android.simsimi', '9.2.3', '1119001'):
        raise AssertionError('Unexpected SimSimi package/version')
    found = {'methods': {}, 'pull_hook': False, 'quick_class': False, 'tap_class': False}
    with zipfile.ZipFile(path) as archive:
        found['hermes_sha256'] = file_hash(archive, 'assets/index.android.bundle')
        for name in archive.namelist():
            if not re.fullmatch(r'classes\d*\.dex', name):
                continue
            dex = DEX(archive.read(name))
            for cls in dex.get_classes():
                owner = cls.get_name()
                found['quick_class'] |= owner == QUICK
                found['tap_class'] |= owner == TAPS
                if owner not in (BAR, CONTROLLER, ACTIVITY):
                    continue
                for method in cls.get_methods():
                    if not method.get_code():
                        continue
                    desc = method.get_descriptor().replace(' ', '')
                    key = (owner, method.get_name(), desc)
                    if ((owner == BAR and method.get_name() in HANDLERS + ('setCurrentItem',)) or
                            (owner == CONTROLLER and method.get_name() == 'onTabSelected' and desc == '(IZ)Z')):
                        assert key not in found['methods'], f'Duplicate method: {key}'
                        found['methods'][key] = {
                            'instructions': [(item.get_name(), item.get_output()) for item in method.get_instructions()],
                            'registers': method.get_code().get_registers_size(),
                        }
                    if owner == ACTIVITY and method.get_name() == 'dispatchTouchEvent':
                        found['pull_hook'] |= any(PULL in item.get_output() for item in method.get_instructions())
            del dex
            gc.collect()
    expected = {(BAR, name, '(ILandroid/view/View;)V') for name in HANDLERS} | {
        (BAR, 'setCurrentItem', '(I)V'), (BAR, 'setCurrentItem', '(IZ)V'),
        (CONTROLLER, 'onTabSelected', '(IZ)Z'),
    }
    assert set(found['methods']) == expected, f'Unexpected native navigation methods: {set(found["methods"])}'
    return found


def check_navigation(old, new, enabled):
    for key, original_method in old['methods'].items():
        method = new['methods'][key]
        assert original_method['registers'] == method['registers'], f'Register layout changed: {key}'
        original_code, actual = original_method['instructions'], method['instructions']
        hooks = [i for i, (_, text) in enumerate(actual) if 'QuickReturn;->onTabClicked(' in text]
        is_click_handler = key[0] == BAR and key[1] in HANDLERS
        if enabled and is_click_handler:
            assert hooks == [0], f'Expected one first-instruction Quick Return click hook: {key}'
            assert actual[0][0] == 'invoke-static', 'Quick Return hook must be a static call'
            assert new['quick_class'] and new['tap_class'], 'Quick Return runtime is missing'
            actual = actual[1:]
        else:
            assert not hooks, f'Unexpected Quick Return injection: {key}'
        assert actual == original_code, f'Original native navigation method changed beyond the click hook: {key}'
    callback = new['methods'][(CONTROLLER, 'onTabSelected', '(IZ)Z')]['instructions']
    assert any('emitBottomTabPressed' in text for _, text in callback), 'Original tab-pressed event was lost'


stock = inspect(original)
both = inspect(combined)
quick = inspect(quick_only)
pull = inspect(pull_only)
check_navigation(stock, both, True)
check_navigation(stock, quick, True)
check_navigation(stock, pull, False)
assert both['pull_hook'], 'Existing pull-to-reload hook missing when both patches are selected'
assert not quick['pull_hook'], 'Quick Return should not force the pull-to-reload patch'
assert pull['pull_hook'], 'Existing pull-to-reload hook missing when selected alone'
assert quick['hermes_sha256'] == stock['hermes_sha256'] == pull['hermes_sha256'], 'Standalone native patches unexpectedly changed Hermes bytecode'
report = {
    'engine': 'Morphe Desktop v1.19.1',
    'input': 'Original uploaded SimSimi 9.2.3 base APK; matching split APKs are required for installation.',
    'quick_return_with_pull_reload': 'passed_static_apk_inspection',
    'quick_return_without_pull_reload': 'passed_static_apk_inspection',
    'pull_reload_without_quick_return': 'passed_static_apk_inspection',
    'classic_and_small_tab_click_handlers_hooked': True,
    'original_click_handlers_continued_unchanged': True,
    'programmatic_set_current_item_unchanged': True,
    'original_tab_callback_preserved': True,
    'standalone_hermes_unchanged': True,
    'simsimi_device_runtime': 'not tested',
    'morphe_manager_android_ui': 'not tested',
}
report_path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
