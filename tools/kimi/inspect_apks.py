#!/usr/bin/env python3
"""Statically inspect the user's Kimi release asset. Never run or publish an APK."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

EXPECTED_ASSET_SHA256 = '7000c991b9e745ccd1d1ecffaff71c2295094cb4a7fce213d3ce1d3310050304'
EXPECTED_ASSET_SIZE = 37729191
MAX_APK_SIZE = 256 * 1024 * 1024
MAX_TOTAL_SIZE = 768 * 1024 * 1024
MAX_APKS = 50

LICENSE = re.compile(r'licen[cs](?:e|ing|ed)|unlicensed|pirac|vending[/.$]licens|notlicensed|未授权|盗版|许可', re.I)
PLAY_LICENSE = re.compile(r'vending[/.$]licens|licen[cs]echecker|licensingservice|check.?license|unlicensed|not.?licensed', re.I)
INTEGRITY = re.compile(r'play[/.$]core[/.$]integrity|app.?integrity|integrity.?token', re.I)
MOD_TOOL = re.compile(r'multi.?patch|lucky.?patch|license.?verification|signature.?killer', re.I)
SENSITIVE = re.compile(r'(?i)(?:https?://|www\.|@|token|secret|password|credential|api.?key|private.?key|bearer|[A-Za-z0-9_+/=-]{48,})')
DEX_NAME = re.compile(r'classes(?:[2-9]|[1-9][0-9]+)?\.dex\Z')
SIGNER_SHA256 = re.compile(r'certificate SHA-256 digest:\s*([0-9a-f]{64})', re.I)
SIGNER_SHA1 = re.compile(r'certificate SHA-1 digest:\s*([0-9a-f]{40})', re.I)


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def check_asset(path: Path) -> None:
    if path.stat().st_size != EXPECTED_ASSET_SIZE or digest_file(path) != EXPECTED_ASSET_SHA256:
        raise ValueError('Release asset bytes do not match the pinned Kimi asset')


def apk_entries(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    """Find bounded inner APK entries without trusting archive paths."""
    infos = archive.infolist()
    names = [info.filename for info in infos]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate APKS archive entries')
    result = []
    total = 0
    for info in infos:
        if info.is_dir() or not info.filename.lower().endswith('.apk'):
            continue
        path = PurePosixPath(info.filename)
        if (path.is_absolute() or '..' in path.parts or '\\' in info.filename
                or any(ord(c) < 32 for c in info.filename) or len(info.filename) > 250):
            raise ValueError('Unsafe APKS entry path')
        if info.flag_bits & 1 or not 0 < info.file_size <= MAX_APK_SIZE:
            raise ValueError('Encrypted or oversized APK entry')
        total += info.file_size
        result.append(info)
    if not result or len(result) > MAX_APKS or total > MAX_TOTAL_SIZE:
        raise ValueError('Unexpected APK count or total size in APKS archive')
    return result


def safe_string(value: str) -> bool:
    """Only retain short printable, non-URL, non-credential-like strings."""
    return (0 < len(value) <= 120 and value.isprintable() and '\n' not in value
            and not SENSITIVE.search(value))


def signature(apksigner: str, apk_path: Path) -> dict:
    # Split manifests can omit minSdk; use the base APK's reviewed minSdk=26.
    result = subprocess.run([apksigner, 'verify', '--verbose', '--print-certs', '--min-sdk-version', '26', str(apk_path)],
                            capture_output=True, text=True, timeout=120, check=False)
    output = result.stdout + '\n' + result.stderr
    sha256 = sorted(set(SIGNER_SHA256.findall(output)))
    sha1 = sorted(set(SIGNER_SHA1.findall(output)))
    return {'verified': result.returncode == 0 and bool(sha256),
            'signer_sha256': [v.lower() for v in sha256], 'signer_sha1': [v.lower() for v in sha1]}


def dex_inventory(apk_path: Path) -> dict:
    from androguard.core.dex import DEX

    classes, methods, strings = set(), set(), set()
    counts = Counter()
    files = []
    with zipfile.ZipFile(apk_path) as apk_zip:
        for info in apk_zip.infolist():
            if not DEX_NAME.fullmatch(info.filename):
                continue
            if not 0 < info.file_size <= MAX_APK_SIZE:
                raise ValueError('Unexpected DEX file size')
            files.append({'name': info.filename, 'bytes': info.file_size})
            dex = DEX(apk_zip.read(info))
            for value in dex.get_strings():
                if not isinstance(value, str):
                    continue
                for key, pattern in [('license', LICENSE), ('play_license', PLAY_LICENSE),
                                     ('integrity', INTEGRITY), ('mod_tool', MOD_TOOL)]:
                    if pattern.search(value):
                        counts[key] += 1
                if LICENSE.search(value) and safe_string(value):
                    strings.add(value)
            for cls in dex.get_classes():
                class_name = cls.get_name()
                if LICENSE.search(class_name) or MOD_TOOL.search(class_name):
                    classes.add(class_name)
                for method in cls.get_methods():
                    name = method.get_name()
                    if LICENSE.search(name) or MOD_TOOL.search(name) or LICENSE.search(class_name):
                        descriptor = re.sub(r'\s+', '', method.get_descriptor())
                        methods.add(f'{class_name}->{name}{descriptor}')
            del dex
            gc.collect()
    return {'dex_files': files, 'matched_string_occurrences': dict(sorted(counts.items())),
            'license_or_tool_class_count': len(classes), 'license_or_tool_classes': sorted(classes)[:180],
            'license_or_tool_method_count': len(methods), 'license_or_tool_methods': sorted(methods)[:240],
            'safe_license_string_count': len(strings), 'safe_license_strings': sorted(strings)[:180],
            'note': 'Strings and names alone are not proof of a runtime license check or bypass.'}


def inspect(apks_path: Path, apksigner: str) -> dict:
    from androguard.core.apk import APK
    from loguru import logger
    logger.remove()
    check_asset(apks_path)
    result = {
        'source': {'release_tag': 'Kimi', 'asset_id': 690272677, 'filename': apks_path.name,
                   'sha256': EXPECTED_ASSET_SHA256, 'bytes': EXPECTED_ASSET_SIZE},
        'scope': 'Static inspection only; the APK was not executed, modified, or redistributed.',
        'components': [],
    }
    with tempfile.TemporaryDirectory(prefix='kimi-apks-') as work, zipfile.ZipFile(apks_path) as outer:
        entries = apk_entries(outer)
        result['outer_non_apk_entries'] = sorted(info.filename for info in outer.infolist()
            if not info.is_dir() and not info.filename.lower().endswith('.apk'))[:30]
        bases = []
        for number, info in enumerate(entries):
            target = Path(work) / f'component-{number}.apk'
            with outer.open(info) as source, target.open('wb') as dest:
                while chunk := source.read(1024 * 1024):
                    dest.write(chunk)
            apk = APK(str(target))
            if not apk.is_valid_APK():
                raise ValueError(f'Invalid inner APK: {info.filename}')
            split_name = apk.get_attribute_value('manifest', 'split') or None
            component = {
                'filename': info.filename, 'bytes': target.stat().st_size, 'sha256': digest_file(target),
                'package': apk.get_package(), 'version_name': apk.get_androidversion_name(),
                'version_code': apk.get_androidversion_code(), 'split': split_name,
                'min_sdk': apk.get_min_sdk_version(), 'target_sdk': apk.get_target_sdk_version(),
                'signature': signature(apksigner, target),
            }
            if not split_name:
                bases.append(component)
                component['main_activity'] = apk.get_main_activity()
                component['license_or_install_permissions'] = sorted(p for p in apk.get_permissions()
                    if re.search(r'LICENSE|BILLING|INSTALL_PACKAGES|QUERY_ALL_PACKAGES', p, re.I))
                with zipfile.ZipFile(target) as inner:
                    names = inner.namelist()
                    component['framework_indicators'] = {
                        'flutter': any('flutter_assets/' in n or n.endswith('/libflutter.so') for n in names),
                        'react_native': any(n.endswith('assets/index.android.bundle') for n in names),
                        'dex': any(DEX_NAME.fullmatch(n) for n in names),
                    }
                    component['native_libraries'] = sorted(n for n in names if n.startswith('lib/') and n.endswith('.so'))[:100]
                component['dex_inspection'] = dex_inventory(target)
            result['components'].append(component)
        if len(bases) != 1:
            raise ValueError(f'Expected exactly one base APK, found {len(bases)}')
        packages = {entry['package'] for entry in result['components']}
        codes = {entry['version_code'] for entry in result['components']}
        names = {entry['version_name'] for entry in result['components'] if entry['version_name']}
        signers = {tuple(entry['signature']['signer_sha256']) for entry in result['components']}
        result['split_consistency'] = {
            'same_package': len(packages) == 1,
            'same_version_code': len(codes) == 1 and bool(next(iter(codes))),
            'explicit_version_names_match': len(names) == 1,
            'same_signers': len(signers) == 1 and bool(next(iter(signers))),
            'all_signatures_verified': all(entry['signature']['verified'] for entry in result['components']),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apks', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--apksigner', required=True)
    args = parser.parse_args()
    report = inspect(args.apks, args.apksigner)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    base = next(c for c in report['components'] if not c['split'])
    print(json.dumps({'package': base['package'], 'version': base['version_name'], 'code': base['version_code'],
                      'apk_components': len(report['components']), 'signature': base['signature'],
                      'frameworks': base['framework_indicators'],
                      'license_method_count': base['dex_inspection']['license_or_tool_method_count'],
                      'split_consistency': report['split_consistency']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
