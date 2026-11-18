#!/usr/bin/env python3
"""Verify the exact GenV remove-ads manifest transformation."""
from __future__ import annotations
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from inspect_genv import DEX_NAME, check_asset
from verify_bundle import ADS, PACKAGE

VERSION = '3.7.2'
CODE = '163'
AD_PERMISSIONS = {'android.permission.ACCESS_ADSERVICES_AD_ID', 'com.google.android.gms.permission.AD_ID'}
AD_METADATA = 'com.google.android.gms.ads.APPLICATION_ID'


def verify_report(path: Path, output: Path) -> None:
    data = json.loads(path.read_text())
    if (data.get('packageName'), data.get('packageVersion')) != (PACKAGE, VERSION):
        raise ValueError('Morphe result does not describe GenV 3.7.2')
    if data.get('success') is not True or data.get('failedPatches') or data.get('appliedPatches') != [ADS]:
        raise ValueError('Exactly the remove-ads selector must succeed')
    if Path(data.get('outputPath', '')).resolve() != output.resolve() or not zipfile.is_zipfile(output):
        raise ValueError('Morphe output is missing or mismatched')


def dex_hashes(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as archive:
        return {info.filename: hashlib.sha256(archive.read(info)).hexdigest()
                for info in archive.infolist() if DEX_NAME.fullmatch(info.filename)}


def manifest_state(path: Path) -> dict:
    from androguard.core.apk import APK
    from loguru import logger
    logger.remove()
    apk = APK(str(path))
    if not apk.is_valid_APK() or (apk.get_package(), apk.get_androidversion_name(), apk.get_androidversion_code()) != (PACKAGE, VERSION, CODE):
        raise ValueError('Unexpected patched APK identity')
    manifest = apk.get_android_manifest_xml()
    android = '{http://schemas.android.com/apk/res/android}'
    applications = list(manifest.iter('application'))
    if len(applications) != 1:
        raise ValueError('Unexpected application element count')
    metadata = [node.get(android + 'name', '') for node in applications[0] if node.tag == 'meta-data']
    return {'permissions': set(apk.get_permissions()), 'metadata': metadata}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('patched', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    check_asset(args.input)
    verify_report(args.report, args.patched)
    before, after = manifest_state(args.input), manifest_state(args.patched)
    if not AD_PERMISSIONS.issubset(before['permissions']) or AD_PERMISSIONS & after['permissions']:
        raise ValueError('Advertising-ID permissions were not removed exactly')
    if 'com.android.vending.BILLING' not in after['permissions']:
        raise ValueError('Billing permission must remain unchanged')
    if AD_METADATA not in before['metadata'] or AD_METADATA in after['metadata']:
        raise ValueError('AdMob application metadata was not removed exactly')
    if before['permissions'] - AD_PERMISSIONS != after['permissions']:
        raise ValueError('An unrelated permission changed')
    if [name for name in before['metadata'] if name != AD_METADATA] != after['metadata']:
        raise ValueError('Unrelated application metadata changed')
    if dex_hashes(args.input) != dex_hashes(args.patched):
        raise ValueError('Manifest-only remove-ads patch changed DEX bytes')
    result = {
        'status': 'passed_actual_mpp_remove_ads_manifest_inspection',
        'selector': ADS, 'package': PACKAGE, 'version': VERSION, 'version_code': CODE,
        'admob_application_id_removed': True,
        'advertising_id_permissions_removed': sorted(AD_PERMISSIONS),
        'billing_permission_preserved': True,
        'dex_files_unchanged': True,
        'premium_plan_credits_purchases_entitlements': 'unchanged by this selector',
        'runtime_ad_delivery_and_flutter_placeholders': 'not tested; complete splits unavailable',
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print('Verified remove-ads manifest-only output; billing and all DEX bytes unchanged')


if __name__ == '__main__':
    main()
