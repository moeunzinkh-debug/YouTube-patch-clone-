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
REGISTRY = 'Ldev/jason/gboardpatches/extension/settings/GboardPatchesSettingsFeatureRegistry;'
TARGETS = {
    ('Lphr;', 'onUpdateSelection', '(IIIIII)V'): RUNTIME + '->onSelection(',
    ('Lphr;', 'onStartInput', '(Landroid/view/inputmethod/EditorInfo;Z)V'): RUNTIME + '->onInputViewStarted(',
    ('Lphr;', 'onStartInputView', '(Landroid/view/inputmethod/EditorInfo;Z)V'): RUNTIME + '->onInputViewStarted(',
    ('Lphr;', 'onFinishInput', '()V'): RUNTIME + '->reset(',
    ('Lphr;', 'onWindowHidden', '()V'): RUNTIME + '->reset(',
    (REGISTRY, 'features', '(Landroid/content/Context;)Ljava/util/List;'): SETTINGS + '->append(',
}
CLASSES = {RUNTIME, SETTINGS,
           'Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishController;',
           'Ldev/jason/gboardpatches/extension/khmerlish/KhmerlishDictionary;'}


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
    source = ROOT / 'tools/gboard-khmer/overlay/patches/src/main/resources/gboard-khmer'
    with zipfile.ZipFile(args.apk) as archive:
        for name in ('dictionary.tsv', 'LICENSE.txt'):
            if archive.read('assets/gboard-khmer/' + name) != (source / name).read_bytes():
                raise SystemExit('Wrong or missing offline dictionary asset: ' + name)
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
            if owner not in {'Lphr;', REGISTRY}:
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
    for key, marker in TARGETS.items():
        if bodies[key].count(marker) != 1:
            raise SystemExit('Missing/duplicate runtime delegate: ' + repr(key))
    selection = bodies[('Lphr;', 'onUpdateSelection', '(IIIIII)V')]
    if 'gboardPatchesCalculatorSelection' not in selection:
        raise SystemExit('Existing calculator selection hook was not preserved in the fixture')
    registry = bodies[(REGISTRY, 'features', '(Landroid/content/Context;)Ljava/util/List;')]
    if registry.index(SETTINGS + '->append(') > registry.index('Ljava/util/Collections;->unmodifiableList('):
        raise SystemExit('Khmerlish settings must be registered before the list is frozen')
    print('Verified Khmerlish settings, lifecycle delegates, dictionary, license and existing calculator hook.')
    print('Fixture is third-party and already patched, not original stock Gboard or a runtime test.')
    print('Fixture output SHA-256:', hashlib.sha256(args.apk.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
