#!/usr/bin/env python3
"""Verify the actual Morphe patch result and reviewed GenV DEX changes."""
from __future__ import annotations
import argparse
import gc
import json
import re
import zipfile
from pathlib import Path
from inspect_genv import ASSET_SHA256, DEX_NAME, check_asset
from verify_bundle import NAME, PACKAGE

VERSION = '3.7.2'
CODE = '163'
CHECK = 'Lcom/pairip/licensecheck/LicenseClient;->checkLicense(Landroid/content/Context;)V'
INITIALIZE = 'Lcom/pairip/licensecheck/LicenseClient;->initializeLicenseCheck()V'
ATTACH = 'Lcom/pairip/application/Application;->attachBaseContext(Landroid/content/Context;)V'
PROVIDER = 'Lcom/pairip/licensecheck/LicenseContentProvider;->onCreate()Z'
BILLING = 'Lcom/android/billingclient/api/Purchase;->equals(Ljava/lang/Object;)Z'
METHODS = {CHECK, INITIALIZE, ATTACH, PROVIDER, BILLING}


def verify_report(path: Path, output: Path) -> None:
    data = json.loads(path.read_text())
    if data.get('packageName') != PACKAGE or data.get('packageVersion') != VERSION:
        raise ValueError('Morphe result does not describe the target GenV APK')
    if data.get('success') is not True or data.get('failedPatches'):
        raise ValueError('Morphe reported a failed or partial patch')
    steps = data.get('stepResults') or []
    if not {'PATCHING', 'REBUILDING'}.issubset({step.get('step') for step in steps}):
        raise ValueError('Morphe did not report both patching and rebuilding')
    if any(step.get('success') is not True for step in steps): raise ValueError('Morphe reported a failed step')
    if data.get('appliedPatches') != [NAME]: raise ValueError('Exactly the requested patch must be applied')
    if Path(data.get('outputPath', '')).resolve() != output.resolve() or not zipfile.is_zipfile(output):
        raise ValueError('Morphe output is missing or does not match the report')


def read_methods(path: Path) -> dict[str, list[tuple[str, str]]]:
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    logger.remove()
    apk = APK(str(path))
    if not apk.is_valid_APK() or apk.get_package() != PACKAGE or apk.get_androidversion_name() != VERSION or apk.get_androidversion_code() != CODE:
        raise ValueError('Unexpected GenV APK identity')
    result = {}
    with zipfile.ZipFile(path) as source:
        for info in source.infolist():
            if not DEX_NAME.fullmatch(info.filename): continue
            if not 0 < info.file_size <= 128 * 1024 * 1024: raise ValueError('Invalid DEX size')
            dex = DEX(source.read(info))
            for cls in dex.get_classes():
                for method in cls.get_methods():
                    key = cls.get_name() + '->' + method.get_name() + ''.join(method.get_descriptor().split())
                    if key not in METHODS: continue
                    if key in result or method.get_code() is None: raise ValueError('Duplicate or bodyless reviewed method: ' + key)
                    result[key] = [(i.get_name(), re.sub(r'\s+', '', i.get_output())) for i in method.get_instructions()]
            del dex
            gc.collect()
    if set(result) != METHODS: raise ValueError('Missing reviewed GenV methods: ' + ', '.join(sorted(METHODS - set(result))))
    return result


def verify_methods(original: dict, patched: dict) -> None:
    for name, size, first in ((CHECK, 16, 'const-string'), (INITIALIZE, 30, 'sget-object')):
        before, after = original[name], patched[name]
        if len(before) != size or before[0][0] != first:
            raise ValueError('Unpatched input has unexpected instructions: ' + name)
        if after != [('return-void', '')] + before:
            raise ValueError('Output differs from the intended early return: ' + name)
    for name in (ATTACH, PROVIDER, BILLING):
        if original[name] != patched[name]: raise ValueError('An unrelated reviewed method changed: ' + name)
    for name in (ATTACH, PROVIDER):
        if not any('Lcom/pairip/licensecheck/LicenseClient;->checkLicense' in args for _, args in original[name]):
            raise ValueError('Reviewed entrypoint does not call PairIP checkLicense: ' + name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('patched', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    check_asset(args.input)
    verify_report(args.report, args.patched)
    verify_methods(read_methods(args.input), read_methods(args.patched))
    with zipfile.ZipFile(args.input) as original, zipfile.ZipFile(args.patched) as modified:
        if original.read('AndroidManifest.xml') != modified.read('AndroidManifest.xml'):
            raise ValueError('Bytecode-only patch unexpectedly changed the manifest')
    check_asset(args.input)
    result = {
        'status': 'passed_actual_mpp_patch_and_dex_inspection',
        'source': 'Read-only GenV release base APK; test output private and not published',
        'package': PACKAGE, 'version': VERSION, 'version_code': CODE,
        'input_sha256': ASSET_SHA256, 'selector': NAME,
        'two_pairip_entrypoints_have_early_return': True,
        'original_entrypoint_bodies_preserved_after_return': True,
        'application_provider_and_reviewed_billing_method_unchanged': True,
        'manifest_unchanged': True,
        'input_requires_splits_and_has_no_native_libraries': True,
        'runtime_live_login_server_attestation_purchases': 'not tested',
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print('Morphe output contains exactly the two reviewed PairIP entry-point changes; selected controls unchanged')

if __name__ == '__main__': main()
