#!/usr/bin/env python3
"""Inspect the rebuilt third-party-derived fixture; never claims stock/device validation."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import zipfile

from loguru import logger
from androguard.core.apk import APK
from androguard.core.dex import DEX

logger.remove()
ROOT = Path(__file__).resolve().parents[2]
RUNTIME = 'Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishRuntime;'
SETTINGS = 'Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishSettingsFeature;'
ACCESS = 'Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishAccessPoint;'
GEMINI_ACCESS = 'Ldev/jason/gboardpatches/extension/geminirouter/GeminiAccessPoint;'
GEMINI_ROUTER = 'Ldev/jason/gboardpatches/extension/geminirouter/GeminiChatRouter;'
REGISTRY = 'Ldev/jason/gboardpatches/extension/settings/GboardPatchesSettingsFeatureRegistry;'
TARGETS = {
    ('Lphr;', 'onUpdateSelection', '(IIIIII)V'): RUNTIME + '->onSelection(',
    ('Lphr;', 'onStartInput', '(Landroid/view/inputmethod/EditorInfo;Z)V'): RUNTIME + '->onInputViewStarted(',
    ('Lphr;', 'onStartInputView', '(Landroid/view/inputmethod/EditorInfo;Z)V'): RUNTIME + '->onInputViewStarted(',
    ('Lphr;', 'onFinishInput', '()V'): RUNTIME + '->reset(',
    ('Lphr;', 'onWindowHidden', '()V'): RUNTIME + '->reset(',
    (REGISTRY, 'features', '(Landroid/content/Context;)Ljava/util/List;'): SETTINGS + '->append(',
    ('Lmvg;', 'm', '(Landroid/content/Context;Lniv;Lnyt;Lwpa;Lwpa;)Lmvg;'): (
        ACCESS + '->extendOrderCatalog(', GEMINI_ACCESS + '->extendOrderCatalog(',
    ),
    ('Lmwv;', '<init>', '(Landroid/content/Context;Lmyc;)V'): (
        ACCESS + '->register(', GEMINI_ACCESS + '->register(',
    ),
}
CLASSES = {RUNTIME, SETTINGS, ACCESS, GEMINI_ACCESS, GEMINI_ROUTER,
           'Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishPanelRuntime;',
           'Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishPanelSession;',
           'Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishPanelConverter;',
           'Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishPanelCommitter;',
           'Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishController;',
           'Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishDictionary;',
           'Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishDictionaryActivity;',
           'Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishPersonalData;',
           'Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishPersonalStore;',
           'Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishWordGuide;'}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    args = parser.parse_args()
    apk = APK(str(args.apk))
    if (apk.get_package(), apk.get_androidversion_name(), apk.get_androidversion_code()) != (
        'com.google.android.inputmethod.latin', '18.5.4.993608717-release-arm64-v8a', '176049702'
    ):
        raise SystemExit('Unexpected test fixture metadata')
    manifest = apk.get_android_manifest_xml()
    android = '{http://schemas.android.com/apk/res/android}'
    markers = [node for node in manifest.iter('meta-data')
               if node.get(android + 'name') == 'dev.jason.gboardpatches.feature.khmerlish']
    if len(markers) != 1 or markers[0].get(android + 'value') != 'true':
        raise SystemExit('Khmerlish settings availability marker missing')
    gemini_markers = [node for node in manifest.iter('meta-data')
                      if node.get(android + 'name') == 'dev.jason.gboardpatches.feature.gemini_router']
    if len(gemini_markers) != 1 or gemini_markers[0].get(android + 'value') != 'true':
        raise SystemExit('Gemini router availability marker missing')
    activities = [node for node in manifest.iter('activity') if node.get(android + 'name')
                  == 'dev.jason.gboardpatches.extension.khmerlish.KhmerlishDictionaryActivity']
    if (len(activities) != 1 or activities[0].get(android + 'exported') != 'false'
            or any(child.tag == 'intent-filter' for child in activities[0])):
        raise SystemExit('Expected one non-exported Khmerlish dictionary activity with no intent filter')
    source = ROOT / 'tools/gboard-khmer/overlay/patches/src/main/resources/gboard-khmer'
    with zipfile.ZipFile(args.apk) as archive:
        for name in ('dictionary.tsv', 'LICENSE.txt'):
            if archive.read('assets/gboard-khmer/' + name) != (source / name).read_bytes():
                raise SystemExit('Wrong or missing offline dictionary asset: ' + name)
        # Androguard 4.1.3 cannot parse all of this Gboard's complex resource
        # table entries. Check the binary string pool and packaged drawable;
        # Android's own resource lookup is additionally exercised in the smoke.
        table = archive.read('resources.arsc')
        for resource_name in ('gboard_khmerlish_panel', 'gboard_gemini_chat'):
            if not any(resource_name.encode(enc) in table for enc in ('utf-8', 'utf-16le')):
                raise SystemExit(resource_name + ' missing from compiled resource table')
            if not any(name.startswith('res/') and name.endswith('/' + resource_name + '.xml')
                       for name in archive.namelist()):
                raise SystemExit('Compiled toolbar drawable is missing: ' + resource_name)
    bodies: dict[tuple[str, str, str], str] = {}
    found = set()
    for data in apk.get_all_dex():
        dex = DEX(data)
        for cls in dex.get_classes():
            owner = cls.get_name()
            if owner in CLASSES:
                if owner in found:
                    raise SystemExit('Duplicate new extension class: ' + owner)
                found.add(owner)
            if owner not in {'Lphr;', 'Lmvg;', 'Lmwv;', REGISTRY}:
                continue
            for method in cls.get_methods():
                key = (owner, method.get_name(), method.get_descriptor().replace(' ', ''))
                if key in TARGETS:
                    if key in bodies or method.get_code() is None:
                        raise SystemExit('Duplicate or absent method body: ' + repr(key))
                    bodies[key] = '\n'.join(ins.get_name() + ' ' + ins.get_output().replace(' ', '')
                                            for ins in method.get_code().get_bc().get_instructions())
    if found != CLASSES or set(bodies) != set(TARGETS):
        raise SystemExit(f'Missing extension classes or native method bodies: {CLASSES - found}, {set(TARGETS) - set(bodies)}')
    for key, markers_for_method in TARGETS.items():
        if isinstance(markers_for_method, str):
            markers_for_method = (markers_for_method,)
        for marker in markers_for_method:
            if bodies[key].count(marker) != 1:
                raise SystemExit('Missing/duplicate runtime delegate: ' + repr((key, marker)))
    selection = bodies[('Lphr;', 'onUpdateSelection', '(IIIIII)V')]
    if 'gboardPatchesCalculatorSelection' not in selection:
        raise SystemExit('Existing calculator selection hook was not preserved in the fixture')
    registry = bodies[(REGISTRY, 'features', '(Landroid/content/Context;)Ljava/util/List;')]
    if registry.index(SETTINGS + '->append(') > registry.index('Ljava/util/Collections;->unmodifiableList('):
        raise SystemExit('Khmerlish settings must be registered before the list is frozen')
    print('Verified Khmerlish and Gemini toolbar delegates, settings, resources and existing calculator hook.')
    print('Fixture is third-party and already patched, not original stock Gboard or a runtime test.')
    print('Fixture output SHA-256:', hashlib.sha256(args.apk.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
