#!/usr/bin/env python3
"""Bounded, read-only static inspection of the user-supplied GenV release APK.

Only package metadata and sanitized license-related class/method structure are
reported. The input is SHA-pinned and is never installed, rewritten or uploaded.
"""
from __future__ import annotations
import argparse
import gc
import hashlib
import json
import re
import subprocess
import zipfile
from collections import Counter
from pathlib import Path

ASSET = 'GenV_3.7.2.apk'
ASSET_SIZE = 23281657
ASSET_SHA256 = 'f50a9d162a5802ce30ba842c09d08c8c2b2c816dc439eb1b8c0346aa71501d2e'
PACKAGE = 'com.ainate.ai.video.generate'
DEX_NAME = re.compile(r'classes(?:[2-9]|[1-9][0-9]+)?\.dex\Z')
LICENSING = re.compile(r'pairip|licen[cs]|licensing|play[/.$]core[/.$]integrity|billing', re.I)
SENSITIVE = re.compile(r'https?://|www\.|@|token|secret|password|credential|api.?key|private.?key|bearer|[A-Za-z0-9_+/=-]{48,}', re.I)
ANDROID = '{http://schemas.android.com/apk/res/android}'
KNOWN = {
    'Lcom/pairip/application/Application;': {'attachBaseContext', 'onCreate'},
    'Lcom/pairip/licensecheck/LicenseClient;': {'checkLicense', 'initializeLicenseCheck', 'isLocalCheckPassed',
        'performLocalInstallerCheck', 'scheduleAppShutdown', 'processResponse'},
    'Lcom/pairip/licensecheck/LicenseContentProvider;': {'onCreate'},
    'Lcom/android/vending/licensing/LicenseChecker;': {'checkAccess'},
    'Lcom/android/vending/licensing/LicenseCheckerCallback;': {'allow', 'dontAllow', 'applicationError'},
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def check_asset(path: Path) -> None:
    if path.name != ASSET or path.stat().st_size != ASSET_SIZE or sha256(path) != ASSET_SHA256:
        raise ValueError('APK does not match the pinned GenV release asset')


def safe_identifier(value: str) -> bool:
    return bool(value) and len(value) <= 220 and value.isprintable() and not SENSITIVE.search(value) and '\n' not in value


def safe_operand(opcode: str, value: str) -> str:
    # No string constants, URLs, credentials or arbitrary application literals.
    if opcode.startswith('const-string') or not safe_identifier(value):
        return '<redacted>'
    return value


def signature(apksigner: str, path: Path, min_sdk: int) -> dict:
    result = subprocess.run([apksigner, 'verify', '--verbose', '--print-certs', '--min-sdk-version', str(min_sdk), str(path)],
                            capture_output=True, text=True, timeout=120, check=False)
    text = result.stdout + '\n' + result.stderr
    sha256s = sorted({x.lower() for x in re.findall(r'certificate SHA-256 digest:\s*([0-9a-f]{64})', text, re.I)})
    sha1s = sorted({x.lower() for x in re.findall(r'certificate SHA-1 digest:\s*([0-9a-f]{40})', text, re.I)})
    return {'verified': result.returncode == 0 and bool(sha256s), 'min_sdk_tested': min_sdk,
            'signer_sha256': sha256s, 'signer_sha1': sha1s}


def inspect(path: Path, apksigner: str) -> dict:
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    logger.remove()
    check_asset(path)
    apk = APK(str(path))
    if not apk.is_valid_APK(): raise ValueError('Input is not a valid APK')
    package = apk.get_package()
    if package != PACKAGE: raise ValueError('Unexpected package identity: ' + str(package))
    min_sdk = int(apk.get_min_sdk_version() or '24')
    manifest = apk.get_android_manifest_xml()
    application = manifest.find('application')
    metadata = []
    if application is not None:
        for element in application.findall('meta-data'):
            name = element.get(ANDROID + 'name', '')
            if 'split' in name.lower() and safe_identifier(name):
                metadata.append({'name': name, 'value': element.get(ANDROID + 'value'), 'resource': element.get(ANDROID + 'resource')})
    result = {
        'scope': 'Read-only static inspection; no target APK execution, modification, upload or account access.',
        'source': {'release_tag': 'GenV', 'asset_id': 723946916, 'filename': ASSET, 'bytes': ASSET_SIZE, 'sha256': ASSET_SHA256},
        'package': package, 'version_name': apk.get_androidversion_name(), 'version_code': apk.get_androidversion_code(),
        'min_sdk': min_sdk, 'target_sdk': apk.get_target_sdk_version(),
        'manifest_split': apk.get_attribute_value('manifest', 'split') or None,
        'is_split_required': apk.get_attribute_value('application', 'isSplitRequired') or apk.get_attribute_value('manifest', 'isSplitRequired') or None,
        'split_metadata': metadata,
        'application_class': apk.get_attribute_value('application', 'name'),
        'main_activity': apk.get_main_activity(),
        'license_or_billing_permissions': sorted(p for p in apk.get_permissions() if re.search(r'LICENSE|BILLING', p, re.I)),
        'signature': signature(apksigner, path, min_sdk),
    }
    classes, methods, callers = set(), set(), set()
    counts = Counter()
    known = {}
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)): raise ValueError('Duplicate ZIP paths')
        libs = sorted(name for name in names if name.startswith('lib/') and name.endswith('.so'))
        result['native_libraries'] = {'count': len(libs), 'abis': sorted({name.split('/')[1] for name in libs if name.count('/') >= 2}),
                                      'flutter': any(name.endswith('/libflutter.so') for name in libs)}
        result['has_flutter_assets'] = any('flutter_assets/' in name for name in names)
        result['pairip_native_or_vm_entries'] = sorted(name for name in names if re.search(r'pairip|\.vmcode(?:/|$)', name, re.I) and safe_identifier(name))[:50]
        result['dex_files'] = []
        for info in infos:
            if not DEX_NAME.fullmatch(info.filename): continue
            if not 0 < info.file_size <= 128 * 1024 * 1024: raise ValueError('Unexpected DEX size')
            result['dex_files'].append({'name': info.filename, 'bytes': info.file_size})
            dex = DEX(archive.read(info))
            for value in dex.get_strings():
                if isinstance(value, str) and LICENSING.search(value):
                    counts['licensing_strings'] += 1
                    if 'pairip' in value.lower(): counts['pairip_strings'] += 1
                    if 'com.android.vending.licensing' in value: counts['classic_service_strings'] += 1
            for cls in dex.get_classes():
                class_name = cls.get_name()
                if LICENSING.search(class_name) and safe_identifier(class_name): classes.add(class_name)
                for method in cls.get_methods():
                    name = method.get_name()
                    descriptor = re.sub(r'\s+', '', method.get_descriptor())
                    identifier = f'{class_name}->{name}{descriptor}'
                    if (LICENSING.search(class_name) or LICENSING.search(name)) and safe_identifier(identifier): methods.add(identifier)
                    if method.get_code() is None: continue
                    selected = name in KNOWN.get(class_name, set())
                    record = None
                    if selected:
                        record = {'dex': info.filename, 'registers': method.get_code().get_registers_size(),
                                  'access_flags': method.get_access_flags_string(), 'opcodes': [], 'references': []}
                    for instruction in method.get_instructions():
                        op, operand = instruction.get_name(), instruction.get_output()
                        if record is not None:
                            if len(record['opcodes']) < 150: record['opcodes'].append(op)
                            if op.startswith(('invoke-', 'iget', 'sget', 'iput', 'sput')) and len(record['references']) < 100:
                                record['references'].append({'opcode': op, 'operand': safe_operand(op, operand)})
                        if op.startswith('invoke-') and re.search(r'Lcom/pairip/(?:licensecheck|application)/|Lcom/android/vending/licensing/', operand):
                            if safe_identifier(identifier) and safe_identifier(operand): callers.add((identifier, operand))
                    if record is not None: known[identifier] = record
            del dex
            gc.collect()
    result['license_string_counts'] = dict(sorted(counts.items()))
    result['matched_classes'] = sorted(classes)[:200]
    result['matched_class_count'] = len(classes)
    result['matched_methods'] = sorted(methods)[:250]
    result['matched_method_count'] = len(methods)
    result['known_entrypoints'] = known
    result['known_license_callers'] = [{'caller': caller, 'invoke': invoke} for caller, invoke in sorted(callers)[:150]]
    result['known_license_caller_count'] = len(callers)
    result['note'] = 'Code identifiers and manifest permissions alone do not prove a live license check or complete APK.'
    check_asset(path)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--apksigner', required=True)
    args = parser.parse_args()
    report = inspect(args.apk, args.apksigner)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'package': report['package'], 'version': report['version_name'], 'version_code': report['version_code'],
                      'dex_count': len(report['dex_files']), 'license_classes': report['matched_class_count'],
                      'known_entrypoints': len(report['known_entrypoints']), 'signature': report['signature'],
                      'native_libraries': report['native_libraries'], 'split_metadata': report['split_metadata']}, ensure_ascii=False))

if __name__ == '__main__': main()
