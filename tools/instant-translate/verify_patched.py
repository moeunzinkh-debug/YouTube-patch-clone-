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
from verify_bundle import NAME, SETTINGS_NAME, PACKAGE, VERSION_NAME

CODE = '50342'
SINGLE = 'Lbe4;->g0(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Lmx1;)Ljava/lang/Object;'
ENDPOINT = 'Lkb9;->S(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Lmx1;)Ljava/lang/Object;'
BATCH = 'Lxm;->D(Ljava/util/List;Ljava/lang/String;Ljava/lang/String;Leh7;Lmx1;)Ljava/lang/Object;'
NATIVE_RETRY = 'Lwx8;->invokeSuspend(Ljava/lang/Object;)Ljava/lang/Object;'
COMBINE = 'Lqu;->emit(Ljava/lang/Object;Llx1;)Ljava/lang/Object;'
ROW = 'Ldv0;->e(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;'
ACTIVITY = 'Lcom/spaceship/screen/translate/ui/MainActivity;->onCreate(Landroid/os/Bundle;)V'
APPLICATION = 'Lcom/spaceship/screen/translate/SSApplication;->onCreate()V'
METHODS = {SINGLE, ENDPOINT, BATCH, NATIVE_RETRY, COMBINE, ROW, ACTIVITY, APPLICATION}
EXTENSION = 'Lapp/morphe/extension/instanttranslate/TranslationFallback;'
CLIENT = 'Lapp/morphe/extension/instanttranslate/GtxClient;'
SETTINGS_UI = 'Lapp/morphe/extension/instanttranslate/SettingsUi;'
SETTINGS_CLICK = 'Lapp/morphe/extension/instanttranslate/SettingsClick;'
SEALION = 'Lapp/morphe/extension/instanttranslate/SeaLionClient;'
PROVIDER_SETTINGS = 'Lapp/morphe/extension/instanttranslate/ProviderSettings;'


def verify_report(path: Path, output: Path, with_settings: bool = False) -> None:
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
    expected = {NAME, SETTINGS_NAME} if with_settings else {NAME}
    applied = data.get('appliedPatches') or []
    if len(applied) != len(expected) or set(applied) != expected:
        raise ValueError('Unexpected opt-in selectors in Morphe patch report')
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
              'settings_ui_methods': set(), 'settings_click_methods': set(), 'sealion_methods': set(),
              'provider_settings_methods': set(), 'function0_definitions': 0,
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
                if owner == SETTINGS_UI:
                    result['settings_ui_methods'].update(method.get_name() for method in cls.get_methods())
                if owner == SETTINGS_CLICK:
                    result['settings_click_methods'].update(method.get_name() for method in cls.get_methods())
                if owner == SEALION:
                    result['sealion_methods'].update(method.get_name() for method in cls.get_methods())
                if owner == PROVIDER_SETTINGS:
                    result['provider_settings_methods'].update(method.get_name() for method in cls.get_methods())
                if owner == 'Lkotlin/jvm/functions/Function0;':
                    result['function0_definitions'] += 1
                if owner not in {'Lbe4;', 'Lkb9;', 'Lxm;', 'Lwx8;', 'Lqu;', 'Ldv0;',
                                 'Lcom/spaceship/screen/translate/ui/MainActivity;',
                                 'Lcom/spaceship/screen/translate/SSApplication;'}:
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


def canonical_body(items: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Remove computed branch offsets while retaining opcodes, registers and references."""
    result = []
    for op, value in items:
        if op.startswith('goto'):
            value = ''
        elif op.startswith(('if-', 'packed-switch', 'sparse-switch')):
            value = value.rsplit(',', 1)[0] if ',' in value else ''
        result.append((op, value))
    return result


def verify_settings_row(before_row: list[tuple[str, str]], after_row: list[tuple[str, str]]) -> None:
    if len(before_row) != 177 or len(after_row) != 195:
        raise ValueError('Unexpected Settings row instruction count')
    injected = after_row[28:46]
    joined = '\n'.join(value for _, value in injected)
    if ('SettingsPatch' not in joined or 'Translationproviders' not in joined or
            SETTINGS_CLICK + '-><init>()V' not in joined or 'Lu44;->v(' not in joined):
        raise ValueError('Settings Patch row or click callback was not installed')
    if injected[-2:] != [('move-object/from16', 'v9,v16'), ('const/4', 'v7,0')]:
        raise ValueError('Compose row did not restore the live composer and zero register')
    if canonical_body(before_row) != canonical_body(after_row[:28] + after_row[46:]):
        raise ValueError('Original Settings rows changed beyond the added row')


def verify_settings(before: dict, after: dict, enabled: bool) -> None:
    if before['function0_definitions'] != 1 or after['function0_definitions'] != 1:
        raise ValueError('Target Kotlin Function0 interface was missing or duplicated')
    if not enabled:
        for name in (ROW, ACTIVITY, APPLICATION):
            if before['methods'][name] != after['methods'][name]:
                raise ValueError('Settings patch modified an unselected Settings method: ' + name)
        return
    verify_settings_row(before['methods'][ROW], after['methods'][ROW])
    for method, hook in ((APPLICATION, 'initialize'), (ACTIVITY, 'attach')):
        original, modified = before['methods'][method], after['methods'][method]
        hook_ref = SETTINGS_UI + '->' + hook
        if sum(hook_ref in value for _, value in modified) != 1:
            raise ValueError('Settings lifecycle hook is missing: ' + method)
        without_hook = [item for item in modified if hook_ref not in item[1]]
        if canonical_body(original) != canonical_body(without_hook):
            raise ValueError('Original lifecycle code changed beyond the settings hook: ' + method)
    integrity = 'Lbin/edisaputra/protector/LicenseActivity;->verifyIntegrity(Landroid/content/Context;)V'
    for current in (before['methods'][ACTIVITY], after['methods'][ACTIVITY]):
        if sum(integrity in value for _, value in current) != 1:
            raise ValueError('Original integrity check was removed or changed')
    expected = (
        ('settings_ui_methods', {'attach', 'initialize', 'open'}),
        ('settings_click_methods', {'invoke'}),
        ('sealion_methods', {'translate', 'parse', 'endpoint'}),
        ('provider_settings_methods', {'initialize', 'save', 'clearKey', 'seaLionConfig'}),
    )
    for key, methods in expected:
        if not methods.issubset(after[key]) or before[key]:
            raise ValueError('Settings extension class or method is missing: ' + key)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', action='store_true', help='expect both the fallback and Settings Patch')
    parser.add_argument('base', type=Path)
    parser.add_argument('patched', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    verify_asset(args.base)
    verify_report(args.report, args.patched, with_settings=args.settings)
    before, after = inspect(args.base), inspect(args.patched)
    verify_methods(before, after)
    verify_settings(before, after, enabled=args.settings)
    result = {
        'status': 'passed_actual_mpp_patch_and_static_dex_checks',
        'package': PACKAGE, 'version': VERSION_NAME, 'version_code': CODE,
        'input_sha256': 'f341a1b174bda7b5d1c95cb2fc84da238228a116844069ee962220acaf1e4e4c',
        'selectors': [NAME, SETTINGS_NAME] if args.settings else [NAME], 'default_enabled': False,
        'single_and_endpoint_fallback_hooks': 2, 'partial_batch_fallback_hooks': 1,
        'settings_row_and_lifecycle_hooks': 'passed' if args.settings else 'not selected; original settings unchanged',
        'original_integrity_check': 'preserved',
        'original_native_retry_and_result_combiner_unchanged': True,
        'runtime': 'not established by this static check',
        'privacy': 'selected fallback sends failed text to Google by default or the explicitly configured SEA-LION endpoint',
    }
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print('Morphe output contains the expected opt-in fallback hooks and preserved native paths')


if __name__ == '__main__':
    main()
