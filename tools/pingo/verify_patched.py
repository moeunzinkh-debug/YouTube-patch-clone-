#!/usr/bin/env python3
"""Verify actual Pingo MPP output at the reviewed DEX methods."""
from __future__ import annotations
import argparse, hashlib, json, re, zipfile
from pathlib import Path

PACKAGE = 'com.picoai.languageapp.android'
VERSION = '5.4.8'
CODE = '941'
BASE_SHA256 = '1ef37fd47d97dae52318ea0a084652d375bccc277e394ab298ab9014234a1c57'
SELECTORS = {'license': 'Remove license check', 'unlock': 'Unlock all feature'}
TARGETS = {
    'check': ('Lcom/pairip/licensecheck/LicenseClient;', 'checkLicense', '(Landroid/content/Context;)V'),
    'initialize': ('Lcom/pairip/licensecheck/LicenseClient;', 'initializeLicenseCheck', '()V'),
    'status': ('Lcom/superwall/sdk/models/entitlements/SubscriptionStatus;', 'isActive', '()Z'),
    'entitlement': ('Lcom/superwall/sdk/models/entitlements/Entitlement;', 'isActive', '()Z'),
}

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_targets(path: Path) -> dict[str, list[tuple[str, str]]]:
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    logger.remove()
    apk = APK(str(path))
    if (not apk.is_valid_APK() or apk.get_package() != PACKAGE or
            apk.get_androidversion_name() != VERSION or apk.get_androidversion_code() != CODE):
        raise ValueError('Unexpected Pingo APK identity')
    found = {key: [] for key in TARGETS}
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not re.fullmatch(r'classes\d*\.dex', name):
                continue
            dex = DEX(archive.read(name))
            for cls in dex.get_classes():
                for key, (class_name, method_name, descriptor) in TARGETS.items():
                    if cls.get_name() != class_name:
                        continue
                    for method in cls.get_methods():
                        if method.get_name() == method_name and ''.join(method.get_descriptor().split()) == descriptor:
                            found[key].append([(ins.get_name(), re.sub(r'\s+', '', ins.get_output()))
                                               for ins in method.get_instructions()])
    for key, values in found.items():
        if len(values) != 1:
            raise ValueError(f'Exact Pingo target {key} count was {len(values)}')
    return {key: values[0] for key, values in found.items()}

def verify_report(report: Path, output: Path, expected: list[str]) -> None:
    data = json.loads(report.read_text())
    if data.get('packageName') != PACKAGE or data.get('packageVersion') != VERSION:
        raise ValueError('Morphe report has the wrong Pingo identity')
    if data.get('success') is not True or data.get('failedPatches') or data.get('appliedPatches') != expected:
        raise ValueError('Morphe did not apply exactly the requested Pingo selectors')
    steps = data.get('stepResults') or []
    if not {'PATCHING', 'REBUILDING'}.issubset({step.get('step') for step in steps}) or any(step.get('success') is not True for step in steps):
        raise ValueError('Morphe did not report successful patching and rebuilding')
    if Path(data.get('outputPath', '')).resolve() != output.resolve() or not zipfile.is_zipfile(output):
        raise ValueError('Morphe output is absent or does not match its report')

def verify_method(original: list[tuple[str, str]], patched: list[tuple[str, str]], prefix: list[tuple[str, str]]) -> None:
    if patched[:len(prefix)] != prefix or patched[len(prefix):] != original:
        raise ValueError('Pingo target did not receive only the reviewed early-return injection')

def verify(base: dict, patched: dict, modes: list[str]) -> None:
    if len(base['check']) != 16 or base['check'][0][0] != 'const-string' or len(base['initialize']) != 29:
        raise ValueError('Reviewed PairIP base fingerprint changed')
    if base['status'] != [('instance-of', 'v0,v1,Lcom/superwall/sdk/models/entitlements/SubscriptionStatus$Active;'), ('return', 'v0')]:
        raise ValueError('Reviewed SubscriptionStatus predicate changed')
    if len(base['entitlement']) != 2 or base['entitlement'][0][0] != 'iget-boolean' or base['entitlement'][1] != ('return', 'v0'):
        raise ValueError('Reviewed Entitlement predicate changed')
    license_on = 'license' in modes
    unlock_on = 'unlock' in modes
    for key in ('check', 'initialize'):
        if license_on:
            verify_method(base[key], patched[key], [('return-void', '')])
        elif patched[key] != base[key]:
            raise ValueError('License target changed while selector was disabled')
    for key in ('status', 'entitlement'):
        if unlock_on:
            verify_method(base[key], patched[key], [('const/4', 'v0,1'), ('return', 'v0')])
        elif patched[key] != base[key]:
            raise ValueError('Unlock target changed while selector was disabled')

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('base', type=Path)
    parser.add_argument('patched', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('output_report', type=Path)
    parser.add_argument('modes', nargs='+', choices=sorted(SELECTORS))
    args = parser.parse_args()
    if digest(args.base) != BASE_SHA256:
        raise ValueError('Not the exact Pingo pre-release APK')
    expected = [SELECTORS[mode] for mode in args.modes]
    verify_report(args.report, args.patched, expected)
    verify(read_targets(args.base), read_targets(args.patched), args.modes)
    result = {
        'status': 'passed_actual_mpp_application_and_dex_inspection',
        'input_sha256': BASE_SHA256, 'package': PACKAGE, 'version': VERSION, 'version_code': CODE,
        'selectors': expected,
        'pairip_early_returns_verified': 'license' in args.modes,
        'superwall_local_active_predicates_verified': 'unlock' in args.modes,
        'server_entitlements_purchases_credits_and_runtime_behavior': 'not tested or granted',
    }
    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.write_text(json.dumps(result, indent=2) + '\n')
    print('Verified exact Pingo injection(s):', ', '.join(expected))

if __name__ == '__main__':
    main()
