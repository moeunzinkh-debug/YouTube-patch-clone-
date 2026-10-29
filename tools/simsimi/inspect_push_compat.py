#!/usr/bin/env python3
"""Inspect public SimSimi and microG RE APKs without accessing a phone or push tokens.

The report records manifest protocol names and a limited list of DEX constant-string
call sites. It does not test notification delivery or infer a device's installed apps.
"""
from __future__ import annotations

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
ANDROID = '{http://schemas.android.com/apk/res/android}'
ORIGINAL_SHA = 'f18da384232c8e918e1073fd2e95cde6dda9bda2a34f4f90bb527ca95ea8af70'
RE_SHA = 'b650b0325de4d80606597003d64ac7b358489c4e5eba6b76dfdc0008e0ca47e4'
TOKENS = (
    'com.google.android.gms', 'app.revanced.android.gms',
    'com.google.iid.TOKEN_REQUEST', 'app.revanced.iid.TOKEN_REQUEST',
    'com.google.android.c2dm.intent.REGISTER', 'app.revanced.android.c2dm.intent.REGISTER',
    'com.google.android.c2dm.intent.RECEIVE', 'app.revanced.android.c2dm.intent.RECEIVE',
    'com.google.android.c2dm.permission.SEND', 'app.revanced.android.c2dm.permission.SEND',
    'com.google.android.c2dm.permission.RECEIVE', 'app.revanced.android.c2dm.permission.RECEIVE',
)
RELEVANT_CALLS = ('->checkPermission(', '->queryBroadcastReceivers(', '->queryIntentServices(',
                  '->sendBroadcast(', '->startService(', '->setPackage(')


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(data)
    return digest.hexdigest()


def manifest(path: Path, package: str) -> dict:
    apk = APK(str(path))
    if apk.get_package() != package:
        raise ValueError(f'Unexpected package in {path.name}: {apk.get_package()}')
    root = apk.get_android_manifest_xml()
    manifest_items = []
    app = root.find('application')
    if app is None:
        raise ValueError('Missing Android application manifest')
    for element in app:
        if element.tag not in ('receiver', 'service'):
            continue
        name = element.get(ANDROID + 'name', '')
        actions = [a.get(ANDROID + 'name', '') for a in element.findall('./intent-filter/action')]
        if not (any(word in name.lower() for word in ('firebase', 'messaging', 'pushregister', 'gcm'))
                or any(word in action.lower() for action in actions
                       for word in ('c2dm', 'iid.token_request', 'firebase.messag'))):
            continue
        manifest_items.append({
            'kind': element.tag,
            'name': name,
            'exported': element.get(ANDROID + 'exported'),
            'permission': element.get(ANDROID + 'permission'),
            'actions': sorted(set(actions)),
        })
    declared = []
    for element in root.findall('permission'):
        name = element.get(ANDROID + 'name', '')
        if 'c2dm' in name.lower():
            declared.append({'name': name, 'protection_level': element.get(ANDROID + 'protectionLevel')})
    requested = sorted(p for p in apk.get_permissions() if 'c2dm' in p.lower()
                       or p.endswith('POST_NOTIFICATIONS') or p.endswith('EXTENDED_ACCESS'))
    return {'package': package, 'version': apk.get_androidversion_name(),
            'version_code': apk.get_androidversion_code(), 'target_sdk': apk.get_target_sdk_version(),
            'requested_permissions': requested, 'declared_c2dm_permissions': declared,
            'messaging_components': manifest_items}


def dex_references(path: Path) -> dict:
    refs = {token: [] for token in TOKENS}
    totals = {token: 0 for token in TOKENS}
    with zipfile.ZipFile(path) as archive:
        for dex_name in archive.namelist():
            if not re.fullmatch(r'classes\d*\.dex', dex_name):
                continue
            data = archive.read(dex_name)
            relevant = tuple(token for token in TOKENS if token.encode() in data)
            if not relevant:
                continue
            dex = DEX(data)
            for cls in dex.get_classes():
                for method in cls.get_methods():
                    if not method.get_code():
                        continue
                    instructions = list(method.get_instructions())
                    hits = set()
                    calls = set()
                    for instruction in instructions:
                        opcode = instruction.get_name()
                        text = instruction.get_output()
                        if opcode.startswith('const-string'):
                            for token in relevant:
                                if '"' + token + '"' in text:
                                    hits.add(token)
                        elif opcode.startswith('invoke-'):
                            calls.update(call for call in RELEVANT_CALLS if call in text)
                    for token in hits:
                        totals[token] += 1
                        if len(refs[token]) < 40:
                            refs[token].append({
                                'dex': dex_name, 'class': cls.get_name(), 'method': method.get_name(),
                                'descriptor': method.get_descriptor(), 'relevant_calls': sorted(calls),
                            })
            del dex, data
            gc.collect()
    return {token: {'method_count': totals[token], 'sample_methods': refs[token]} for token in TOKENS}


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit('usage: inspect_push_compat.py original.apk patched.apk microg-re.apk report.json')
    original, patched, microg, output = map(Path, sys.argv[1:])
    if sha256(original) != ORIGINAL_SHA or sha256(microg) != RE_SHA:
        raise SystemExit('Input hash differs from the pinned public release asset')
    stock_manifest = manifest(original, 'com.ismaker.android.simsimi')
    patched_manifest = manifest(patched, 'com.ismaker.android.simsimi')
    re_manifest = manifest(microg, 'app.revanced.android.gms')
    if (stock_manifest['version'], stock_manifest['version_code'], re_manifest['version']) != ('9.2.3', '1119001', '7.3.0-dev.2'):
        raise SystemExit('Unexpected release version; refusing to compare')
    result = {
        'scope': 'Static inspection of public APK artifacts; no Android device or live push delivery tested.',
        'microg_re_release_sha256': RE_SHA,
        'simsimi_original_sha256': ORIGINAL_SHA,
        'simsimi_stock': stock_manifest,
        'simsimi_patched_microg_only': patched_manifest,
        'microg_re': re_manifest,
        'stock_dex_references': dex_references(original),
        'patched_dex_references': dex_references(patched),
    }
    output.write_text(json.dumps(result, indent=2) + '\n')
    print('Wrote sanitized manifest and DEX protocol comparison:', output)


if __name__ == '__main__':
    main()
