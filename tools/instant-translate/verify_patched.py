#!/usr/bin/env python3
"""Verify actual Morphe output and injection points; this does not prove runtime translation."""
from __future__ import annotations

import argparse
import gc
import json
import re
import zipfile
from pathlib import Path

from inspect_apk import DEX_NAME, verify_asset
from verify_bundle import NAME, PACKAGE, VERSION_NAME

CODE = '50342'
SINGLE = 'Lbe4;->g0(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Lmx1;)Ljava/lang/Object;'
ENDPOINT = 'Lkb9;->S(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Lmx1;)Ljava/lang/Object;'
BATCH = 'Lxm;->D(Ljava/util/List;Ljava/lang/String;Ljava/lang/String;Leh7;Lmx1;)Ljava/lang/Object;'
NATIVE_RETRY = 'Lwx8;->invokeSuspend(Ljava/lang/Object;)Ljava/lang/Object;'
COMBINE = 'Lqu;->emit(Ljava/lang/Object;Llx1;)Ljava/lang/Object;'
METHODS = {SINGLE, ENDPOINT, BATCH, NATIVE_RETRY, COMBINE}
EXTENSION = 'Lapp/morphe/extension/instanttranslate/TranslationFallback;'
CLIENT = 'Lapp/morphe/extension/instanttranslate/GtxClient;'


def verify_report(path: Path, output: Path) -> None:
    data = json.loads(path.read_text())
    if data.get('packageName') != PACKAGE or data.get('packageVersion') != VERSION_NAME:
        raise ValueError('Morphe report has a different package or version')
    if data.get('success') is not True or data.get('failedPatches'):
        raise ValueError('Morphe reported a failed patch')
    steps = data.get('stepResults') or []
    if not {'PATCHING', 'REBUILDING'}.issubset({step.get('step') for step in steps}):
        raise ValueError('Morphe did not report patching and rebuilding')
    if any(step.get('success') is not True for step in steps):
        raise ValueError('Morphe reported a failed step')
    if data.get('appliedPatches') != [NAME]:
        raise ValueError('Exactly the opt-in translation patch was not applied')
    if Path(data.get('outputPath', '')).resolve() != output.resolve() or not zipfile.is_zipfile(output):
        raise ValueError('Morphe output is missing or differs from report')


def inspect(path: Path) -> dict:
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    logger.remove()
    apk = APK(str(path))
    if not apk.is_valid_APK() or apk.get_package() != PACKAGE or apk.get_androidversion_name() != VERSION_NAME or apk.get_androidversion_code() != CODE:
        raise ValueError('Unexpected APK identity')
    result = {'methods': {}, 'fields': {}, 'extension_methods': set(), 'client_methods': set(),
              'internet': 'android.permission.INTERNET' in apk.get_permissions()}
    with zipfile.ZipFile(path) as source:
        for info in source.infolist():
            if not DEX_NAME.fullmatch(info.filename):
                continue
            dex = DEX(source.read(info))
            for cls in dex.get_classes():
                owner = cls.get_name()
                if owner in {'Ld29;', 'Lqy8;', 'Lmr0;'}:
                    result['fields'][owner] = sorted((field.get_name(), field.get_descriptor()) for field in cls.get_fields())
                if owner == EXTENSION:
                    result['extension_methods'].update(method.get_name() for method in cls.get_methods())
                if owner == CLIENT:
                    result['client_methods'].update(method.get_name() for method in cls.get_methods())
                if owner not in {'Lbe4;', 'Lkb9;', 'Lxm;', 'Lwx8;', 'Lqu;'}:
                    continue
                for method in cls.get_methods():
                    key = owner + '->' + method.get_name() + ''.join(method.get_descriptor().split())
                    if key not in METHODS:
                        continue
                    if key in result['methods'] or method.get_code() is None:
                        raise ValueError('Target method duplicate or has no code: ' + key)
                    result['methods'][key] = [(item.get_name(), re.sub(r'\s+', '', item.get_output())) for item in method.get_instructions()]
            del dex
            gc.collect()
    if set(result['methods']) != METHODS:
        raise ValueError('Some reviewed methods were missing')
    return result


def verify_methods(before: dict, after: dict) -> None:
    if not before['internet'] or not after['internet']:
        raise ValueError('Internet permission is missing')
    for name in (NATIVE_RETRY, COMBINE):
        if before['methods'][name] != after['methods'][name]:
            raise ValueError('An unrelated native retry/result-combiner body changed: ' + name)
    checks = ((SINGLE, 'retryAfterBlank', 'Lus9;-><init>', 'Lbe4;->Z'),
              (ENDPOINT, 'retryAfterBlank', 'Lkb9;->V', 'Lld8;->v0'),
              (BATCH, 'retryFailedBatch', 'Lxm;->E', 'Ltk7;->resumeWith'))
    for method, hook, *native_refs in checks:
        original, patched = before['methods'][method], after['methods'][method]
        native = '\n'.join(value for _, value in original)
        edited = '\n'.join(value for _, value in patched)
        if edited.count(EXTENSION + '->' + hook) != 1 or EXTENSION in native:
            raise ValueError('Expected precisely one new fallback hook: ' + method)
        for ref in native_refs:
            if ref not in native or ref not in edited:
                raise ValueError('Original translation path reference missing: ' + ref)
        if 'Ltk3;->Q(Llx1;)Llx1;' not in edited:
            raise ValueError('Intercepted continuation missing: ' + method)
    single = '\n'.join(value for _, value in after['methods'][SINGLE])
    if 'Ld29;->morphe_source' not in single or 'Ld29;->morphe_target' not in single:
        raise ValueError('Coroutine language captures are missing')
    added_fields = set(after['fields']['Ld29;']) - set(before['fields']['Ld29;'])
    if added_fields != {('morphe_source', 'Ljava/lang/String;'), ('morphe_target', 'Ljava/lang/String;')}:
        raise ValueError('Unexpected coroutine field changes')
    for owner in ('Lqy8;', 'Lmr0;'):
        if before['fields'][owner] != after['fields'][owner]:
            raise ValueError('Unexpected coroutine fields changed: ' + owner)
    if not {'retryAfterBlank', 'retryFailedBatch'}.issubset(after['extension_methods']) or 'translate' not in after['client_methods']:
        raise ValueError('Fallback runtime extension was not merged')
    if before['extension_methods'] or before['client_methods']:
        raise ValueError('Unexpected extension already present in input')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base', type=Path)
    parser.add_argument('patched', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    verify_asset(args.base)
    verify_report(args.report, args.patched)
    verify_methods(inspect(args.base), inspect(args.patched))
    result = {
        'status': 'passed_actual_mpp_patch_and_static_dex_checks',
        'package': PACKAGE, 'version': VERSION_NAME, 'version_code': CODE,
        'input_sha256': 'f341a1b174bda7b5d1c95cb2fc84da238228a116844069ee962220acaf1e4e4c',
        'selector': NAME, 'default_enabled': False,
        'single_and_endpoint_fallback_hooks': 2, 'partial_batch_fallback_hooks': 1,
        'original_native_retry_and_result_combiner_unchanged': True,
        'runtime': 'not established by this static check',
        'privacy': 'selected fallback sends failed text to translate.googleapis.com over HTTPS',
    }
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print('Morphe output contains the expected opt-in fallback hooks and preserved native paths')


if __name__ == '__main__':
    main()
