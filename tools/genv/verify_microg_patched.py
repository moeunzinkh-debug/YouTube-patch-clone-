#!/usr/bin/env python3
"""Inspect disposable GenV outputs for reviewed MicroG routing, never login data.

Only fixed counts and public APK identifiers are written. Arbitrary APK strings
are hashed in memory for before/after comparison and are never printed or saved.
"""
from __future__ import annotations
import argparse
import copy
import gc
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET

from inspect_genv import ASSET_SHA256, DEX_NAME, check_asset
from inspect_google_auth import extract_route
from verify_bundle import MICROG, NAME, PACKAGE

VERSION, CODE = '3.7.2', '163'
AVAILABILITY = 'Li3/f;->b(Landroid/content/Context;I)I'
GUARD = 'Lapp/morphe/extension/genv/MicroGGuard;'
ANDROID = '{http://schemas.android.com/apk/res/android}'
EXPECTED_METADATA = {
    'app.revanced.android.gms.SPOOFED_PACKAGE_NAME': PACKAGE,
    'app.revanced.android.gms.SPOOFED_PACKAGE_SIGNATURE': 'be4c81d3869d726ea9f0229ab937f2e11ab1ccc7',
    'app.revanced.MICROG_PACKAGE_NAME': 'app.revanced.android.gms',
}
ROUTES = {
    'com.google': 7,
    'com.google.android.gms': 44,
    'com.google.android.gms.auth.GOOGLE_SIGN_IN': 2,
    'com.google.android.gms.auth.account.authapi.START': 1,
    'com.google.android.gms.auth.api.credentials.service.START': 1,
    'com.google.android.gms.auth.api.signin.service.START': 1,
    'com.google.android.gms.signin.service.START': 1,
    'com.google.android.gms.chimera': 3,
    'com.google.android.gms.phenotype': 4,
    'com.google.android.gms.common.telemetry.service.START': 1,
    'com.google.android.gms.gass.START': 1,
    'com.google.android.gms.measurement.START': 3,
    'com.google.android.c2dm.intent.RECEIVE': 2,
    'com.google.android.c2dm.intent.REGISTER': 4,
    'com.google.android.c2dm.intent.REGISTRATION': 1,
    'com.google.android.c2dm.permission.SEND': 2,
    'com.google.android.gtalkservice.permission.GTALK_SERVICE': 1,
    'content://com.google.android.gsf.gservices': 2,
}


def digest(value: str) -> bytes:
    return hashlib.sha256(value.encode('utf-8')).digest()


def inspect_dex(path: Path, original: bool) -> tuple[dict, Counter, list, bool]:
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    logger.remove()
    apk = APK(str(path))
    if not apk.is_valid_APK() or apk.get_package() != PACKAGE or apk.get_androidversion_name() != VERSION or apk.get_androidversion_code() != CODE:
        raise ValueError('Unexpected GenV APK identity')
    methods, counts, availability, guard = {}, Counter(), [], False
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if not DEX_NAME.fullmatch(info.filename): continue
            if not 0 < info.file_size <= 128 * 1024 * 1024: raise ValueError('Invalid DEX size')
            dex = DEX(archive.read(info))
            for cls in dex.get_classes():
                if cls.get_name() == GUARD: guard = True
                for method in cls.get_methods():
                    if method.get_code() is None: continue
                    key = cls.get_name() + '->' + method.get_name() + ''.join(method.get_descriptor().split())
                    consts = []
                    for instruction in method.get_instructions():
                        op, operand = instruction.get_name(), instruction.get_output()
                        if op in ('const-string', 'const-string/jumbo'):
                            route = extract_route(operand) if original else None
                            if route in ROUTES:
                                counts[route] += 1
                                operand = operand.replace('"' + route + '"', '"' + route.replace('com.google', 'app.revanced', 1) + '"')
                            consts.append(digest(op + '\0' + operand))
                        if key == AVAILABILITY:
                            ref_off = instruction.get_ref_off() if op == 'if-eqz' and hasattr(instruction, 'get_ref_off') else None
                            availability.append((op, operand, instruction.get_length(), ref_off))
                    if consts:
                        if key in methods: raise ValueError('Duplicate method in DEX')
                        methods[key] = consts
            del dex
            gc.collect()
    return methods, counts, availability, guard


def verify_availability(before: list, after: list) -> None:
    if len(before) != 284 or len(after) != 290:
        raise ValueError('Unexpected availability method shape')
    expected_prefix = ['invoke-static/range', 'move-result', 'if-eqz', 'const/4', 'return', 'nop']
    if [row[0] for row in after[:6]] != expected_prefix or [row[0] for row in before] != [row[0] for row in after[6:]]:
        raise ValueError('Unexpected availability guard or changed original opcode sequence')
    if GUARD + '->isAvailable(Landroid/content/Context;)Z' not in ''.join(after[0][1].split()):
        raise ValueError('Availability guard does not call the MicroG verifier')
    if 'v10' not in after[0][1] or 'v0' not in after[1][1] or 'v0' not in after[4][1]:
        raise ValueError('Unexpected availability guard register mapping')
    # The conditional false path must point at the nop immediately before the
    # original body. DEX branch offsets are signed 16-bit code units.
    branch = sum(row[2] for row in after[:2])
    target = sum(row[2] for row in after[:5])
    if after[2][3] is None or branch + 2 * after[2][3] != target:
        raise ValueError('Availability guard does not fall back to the original method')
    if not re.fullmatch(r'v0,\s*(?:0|0x0)', after[3][1]):
        raise ValueError('Availability success is not zero')


def _normal_tree(node: ET.Element, patched: bool = False):
    attrs = {}
    for key, value in node.attrib.items():
        if patched and key in {ANDROID + x for x in ('name', 'permission', 'readPermission', 'writePermission')}:
            if value.startswith('app.revanced.android.c2dm.') or value == 'app.revanced.android.gtalkservice.permission.GTALK_SERVICE':
                value = value.replace('app.revanced', 'com.google', 1)
        attrs[key] = value
    return node.tag, tuple(sorted(attrs.items())), tuple(_normal_tree(child, patched) for child in node)


def verify_manifest(before: ET.Element, after: ET.Element) -> None:
    before, after = copy.deepcopy(before), copy.deepcopy(after)
    if before.get('package') != PACKAGE or after.get('package') != PACKAGE:
        raise ValueError('GenV package changed')
    old_app, new_app = before.find('application'), after.find('application')
    if old_app is None or new_app is None: raise ValueError('Missing application manifest element')
    for key, value in EXPECTED_METADATA.items():
        old = [x for x in old_app.findall('meta-data') if x.get(ANDROID + 'name') == key]
        found = [x for x in new_app.findall('meta-data') if x.get(ANDROID + 'name') == key]
        if old or len(found) != 1 or found[0].get(ANDROID + 'value') != value:
            raise ValueError('Missing or conflicting reviewed MicroG metadata')
        new_app.remove(found[0])
    old_queries, new_queries = before.findall('queries'), after.findall('queries')
    if len(old_queries) > 1 or len(new_queries) != 1: raise ValueError('Unexpected queries structure')
    target = 'app.revanced.android.gms'
    if old_queries and any(x.get(ANDROID + 'name') == target for x in old_queries[0].findall('package')):
        raise ValueError('Original already had Morphe package query')
    matches = [x for x in new_queries[0].findall('package') if x.get(ANDROID + 'name') == target]
    if len(matches) != 1: raise ValueError('Morphe package visibility missing or duplicated')
    new_queries[0].remove(matches[0])
    if not old_queries:
        if len(new_queries[0]) or new_queries[0].attrib: raise ValueError('Unexpected added queries')
        after.remove(new_queries[0])
    if _normal_tree(before) != _normal_tree(after, patched=True):
        raise ValueError('Manifest differs beyond reviewed MicroG entries and C2DM routing')


def manifest(path: Path) -> ET.Element:
    from androguard.core.apk import APK
    from lxml import etree
    value = APK(str(path)).get_android_manifest_xml()
    if value is None: raise ValueError('APK manifest could not be decoded')
    return ET.fromstring(etree.tostring(value))


def verify_report(path: Path, output: Path, selectors: set[str]) -> None:
    result = json.loads(path.read_text())
    if result.get('packageName') != PACKAGE or result.get('packageVersion') != VERSION or result.get('success') is not True or result.get('failedPatches'):
        raise ValueError('Morphe reported an unsuccessful or unexpected patch')
    selected = result.get('appliedPatches') or []
    if len(selected) != len(selectors) or set(selected) != selectors:
        raise ValueError('Unexpected applied selector set')
    steps = result.get('stepResults') or []
    if not {'PATCHING', 'REBUILDING'}.issubset({s.get('step') for s in steps}) or any(s.get('success') is not True for s in steps):
        raise ValueError('Morphe patching or rebuilding step failed')
    if Path(result.get('outputPath', '')).resolve() != output.resolve() or not zipfile.is_zipfile(output):
        raise ValueError('Morphe output missing')


def verify_contents(source: Path, outputs: list[Path]) -> dict:
    check_asset(source)
    original_methods, counts, old_availability, old_guard = inspect_dex(source, original=True)
    if dict(counts) != ROUTES or old_guard: raise ValueError('Source APK does not match the reviewed routing fingerprint')
    source_manifest = manifest(source)
    for output in outputs:
        methods, _, availability, guard = inspect_dex(output, original=False)
        if not guard: raise ValueError('Compiled MicroG verifier extension missing from output')
        if any(methods.get(key) != values for key, values in original_methods.items()):
            raise ValueError('A DEX string differs beyond the reviewed route substitutions')
        verify_availability(old_availability, availability)
        verify_manifest(source_manifest, manifest(output))
    check_asset(source)
    return {
        'status': 'passed_morphe_microg_static', 'input_sha256': ASSET_SHA256,
        'package': PACKAGE, 'version': VERSION, 'version_code': CODE,
        'route_sites_checked': sum(ROUTES.values()), 'route_literal_kinds': len(ROUTES),
        'other_original_dex_strings_unchanged': True, 'binder_descriptors_unchanged': True,
        'microg_signer_and_signin_components_guarded': True,
        'original_availability_control_flow_retained_with_routed_literals': True,
        'original_genv_signer_metadata_sha1': EXPECTED_METADATA['app.revanced.android.gms.SPOOFED_PACKAGE_SIGNATURE'],
        'source_signer_certificate_checked_before_metadata': True,
        'manifest_only_reviewed_metadata_queries_and_c2dm': True,
        'actual_login_firebase_server_and_complete_split_app_runtime': 'not tested',
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('microg_only', type=Path)
    parser.add_argument('microg_report', type=Path)
    parser.add_argument('both', type=Path)
    parser.add_argument('both_report', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    verify_report(args.microg_report, args.microg_only, {MICROG})
    verify_report(args.both_report, args.both, {NAME, MICROG})
    result = verify_contents(args.input, [args.microg_only, args.both])
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print('Verified reviewed routes, unchanged other DEX strings, scoped manifest entries and conditional availability in both disposable outputs')


if __name__ == '__main__':
    main()
