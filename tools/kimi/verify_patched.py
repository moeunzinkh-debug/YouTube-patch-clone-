#!/usr/bin/env python3
"""Check real Morphe results and the exact Kimi DEX modifications, not live login."""
from __future__ import annotations

import argparse
import gc
import json
import re
import zipfile
from pathlib import Path

from inspect_apks import DEX_NAME, digest_file
from verify_bundle import NAME, PACKAGE

VERSION = '3.1.5'
CODE = '381'
BASE_SHA256 = 'b7a5a412ed6958823da4b513523a22da2b032578f651fd9f9d4d08e4fc0ff85d'
CHECK = 'Lcom/pairip/licensecheck/LicenseClient;->checkLicense(Landroid/content/Context;)V'
INITIALIZE = 'Lcom/pairip/licensecheck/LicenseClient;->initializeLicenseCheck()V'
ATTACH = 'Lcom/pairip/application/Application;->attachBaseContext(Landroid/content/Context;)V'
PROVIDER = 'Lcom/pairip/licensecheck/LicenseContentProvider;->onCreate()Z'
TENCENT = ('Lcom/tencent/liteav/sdk/common/LicenseChecker;->setLicense'
           '(Lcom/tencent/liteav/sdk/common/LicenseChecker$c;Ljava/lang/String;Ljava/lang/String;)Z')
METHODS = {CHECK, INITIALIZE, ATTACH, PROVIDER, TENCENT}


def verify_report(path: Path, output: Path) -> None:
    data = json.loads(path.read_text())
    if data.get('packageName') != PACKAGE or data.get('packageVersion') != VERSION:
        raise ValueError('Morphe report does not describe the target Kimi APK')
    if data.get('success') is not True or data.get('failedPatches'):
        raise ValueError('Morphe reported a failed or partial patch')
    steps = data.get('stepResults') or []
    if not {'PATCHING', 'REBUILDING'}.issubset({step.get('step') for step in steps}):
        raise ValueError('Morphe did not report both patching and rebuilding')
    if any(step.get('success') is not True for step in steps):
        raise ValueError('Morphe reported a failed step')
    if data.get('appliedPatches') != [NAME]:
        raise ValueError('Morphe did not apply exactly the requested selector')
    if Path(data.get('outputPath', '')).resolve() != output.resolve() or not zipfile.is_zipfile(output):
        raise ValueError('Morphe output is missing or does not match the report')


def read_methods(path: Path) -> dict[str, list[tuple[str, str]]]:
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    logger.remove()
    apk = APK(str(path))
    if not apk.is_valid_APK() or apk.get_package() != PACKAGE or apk.get_androidversion_name() != VERSION or apk.get_androidversion_code() != CODE:
        raise ValueError('Unexpected Kimi APK identity')
    result = {}
    with zipfile.ZipFile(path) as source:
        for info in source.infolist():
            if not DEX_NAME.fullmatch(info.filename):
                continue
            dex = DEX(source.read(info))
            for cls in dex.get_classes():
                for method in cls.get_methods():
                    key = cls.get_name() + '->' + method.get_name() + ''.join(method.get_descriptor().split())
                    if key not in METHODS:
                        continue
                    if key in result or method.get_code() is None:
                        raise ValueError('Duplicate or bodyless target: ' + key)
                    result[key] = [(i.get_name(), re.sub(r'\s+', '', i.get_output())) for i in method.get_instructions()]
            del dex
            gc.collect()
    if set(result) != METHODS:
        raise ValueError('Missing reviewed Kimi method: ' + ', '.join(sorted(METHODS - set(result))))
    return result


def verify_methods(original: dict, patched: dict) -> None:
    for name, size, first in ((CHECK, 16, 'const-string'), (INITIALIZE, 29, 'sget-object')):
        before, after = original[name], patched[name]
        if len(before) != size or before[0][0] != first:
            raise ValueError('The unpatched input has an unexpected method layout: ' + name)
        if after != [('return-void', '')] + before:
            raise ValueError('Morphe output differs from the intended early return: ' + name)
    for name in (ATTACH, PROVIDER, TENCENT):
        if original[name] != patched[name]:
            raise ValueError('An unrelated entrypoint or Tencent license method changed: ' + name)
    if not any('Lcom/pairip/licensecheck/LicenseClient;->checkLicense' in operands
               for _, operands in original[ATTACH]):
        raise ValueError('The reviewed application startup does not call PairIP checkLicense')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base', type=Path)
    parser.add_argument('patched', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    if digest_file(args.base) != BASE_SHA256:
        raise ValueError('Not the reviewed base APK from the user-supplied APKS archive')
    verify_report(args.report, args.patched)
    verify_methods(read_methods(args.base), read_methods(args.patched))
    result = {
        'status': 'passed_actual_mpp_patch_and_dex_inspection',
        'source': 'Kimi release asset 690272677, supplied already re-signed APKS; base APK only',
        'package': PACKAGE, 'version': VERSION, 'version_code': CODE,
        'input_base_sha256': BASE_SHA256, 'selector': NAME,
        'two_pairip_entrypoints_have_early_return': True,
        'original_entrypoint_bodies_preserved_after_return': True,
        'application_and_provider_call_sites_unchanged': True,
        'tencent_license_method_unchanged': True,
        'split_merge_manager_and_runtime': 'not tested by this Desktop/base-APK check',
        'live_login_server_attestation_and_paid_features': 'not tested',
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print('Real Morphe output contains the two expected PairIP-only entry-point changes')


if __name__ == '__main__':
    main()
