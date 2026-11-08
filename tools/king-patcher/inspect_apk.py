#!/usr/bin/env python3
"""Read-only, bounded static inventory of the user-provided King-Patcher APK.

The APK is pinned to its release digest. Do not modify, install or distribute it.
Only short non-credential-like strings and code identifiers enter the report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ASSET_NAME = 'King.Patcher_12.10.10.apk'
ASSET_SIZE = 15071570
ASSET_SHA256 = 'e37e25e0fdb2ea92a1592eec7251488d235136e85d5f4e8400f74f8910f40222'
DEX_NAME = re.compile(r'classes(?:[2-9]|[1-9][0-9]+)?\.dex\Z')
SENSITIVE = re.compile(r'(?:https?://|www\.|@|token|secret|password|credential|api.?key|private.?key|bearer|[A-Za-z0-9_+/=-]{48,})', re.I)
MENU = re.compile(r'(?:licen[cs](?:e|ing)|verif(?:y|ication)|modify|modified|rebuild|patch|re.?sign|permission|activit|signature|advert|insignificant)', re.I)
SCREEN = re.compile(r'(?:create.*(?:modified|patch).*apk|apk.*(?:without|licen[cs]|modif|patch)|license verification|multi.?patch)', re.I)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def safe(value: str) -> bool:
    return 0 < len(value) <= 180 and value.isprintable() and not SENSITIVE.search(value)


def check_asset(path: Path) -> None:
    if path.name != ASSET_NAME or path.stat().st_size != ASSET_SIZE or sha256(path) != ASSET_SHA256:
        raise ValueError('APK does not match the exact reviewed release asset')


def resource_inventory(decoded: Path) -> dict:
    """Find candidate English UI labels and their public resource IDs."""
    resources = decoded / 'res'
    if not resources.is_dir():
        return {'available': False, 'message': 'Resource decoding unavailable'}
    ids = {}
    public = resources / 'values/public.xml'
    if public.exists():
        for node in ET.parse(public).getroot():
            if node.get('type') == 'string' and node.get('name') and node.get('id'):
                ids[node.get('name')] = node.get('id')
    labels = {}
    for directory in (resources / 'values', resources / 'values-en', resources / 'values-en-rUS'):
        strings = directory / 'strings.xml'
        if not strings.exists():
            continue
        for node in ET.parse(strings).getroot():
            if node.tag != 'string' or not node.get('name'):
                continue
            value = ' '.join(''.join(node.itertext()).split())
            if safe(value) and MENU.search(value):
                key = (node.get('name'), value)
                labels[key] = {'name': node.get('name'), 'value': value,
                               'id': ids.get(node.get('name')), 'locale': directory.name}
    items = sorted(labels.values(), key=lambda item: (not bool(SCREEN.search(item['value'])), item['name'], item['value']))
    return {'available': True, 'matching_label_count': len(items), 'labels': items[:180],
            'screen_candidates': [item for item in items if SCREEN.search(item['value'])][:60]}


def smali_references(decoded: Path, candidates: list[dict]) -> dict:
    """Locate methods referencing known menu string resources, without storing smali code."""
    keys = {}
    for item in candidates:
        if item.get('id'):
            keys[item['id'].lower()] = item['name']
        keys['->' + item['name'].lower() + ':'] = item['name']
    if not keys:
        return {'files_scanned': 0, 'references': []}
    result = set()
    count = 0
    for root in sorted(decoded.glob('smali*')):
        if not root.is_dir():
            continue
        for path in root.rglob('*.smali'):
            count += 1
            klass = method = None
            try:
                with path.open('r', encoding='utf-8', errors='replace') as stream:
                    for line in stream:
                        line = line.strip()
                        if line.startswith('.class '):
                            klass = line.split()[-1]
                        elif line.startswith('.method '):
                            method = line.removeprefix('.method ').split()[-1]
                        elif line == '.end method':
                            method = None
                        low = line.lower()
                        if klass and method:
                            for needle, name in keys.items():
                                if needle in low:
                                    result.add((klass, method, name))
            except OSError:
                continue
    values = [{'class': k, 'method': m, 'resource': n} for k, m, n in sorted(result)]
    return {'files_scanned': count, 'reference_count': len(values), 'references': values[:250]}


def dex_inventory(path: Path) -> dict:
    from androguard.core.dex import DEX

    strings, classes, methods = set(), set(), set()
    dex_files = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if not DEX_NAME.fullmatch(info.filename):
                continue
            if not 0 < info.file_size <= 120 * 1024 * 1024:
                raise ValueError('Unexpected DEX size')
            dex_files.append({'name': info.filename, 'bytes': info.file_size})
            dex = DEX(archive.read(info))
            for value in dex.get_strings():
                if isinstance(value, str) and MENU.search(value) and safe(value):
                    strings.add(value)
            for cls in dex.get_classes():
                klass = cls.get_name()
                if MENU.search(klass) and safe(klass):
                    classes.add(klass)
                for method in cls.get_methods():
                    name = method.get_name()
                    if MENU.search(name) and safe(klass) and safe(name):
                        descriptor = re.sub(r'\s+', '', method.get_descriptor())
                        methods.add(f'{klass}->{name}{descriptor}')
    ranked = sorted(strings, key=lambda value: (not bool(SCREEN.search(value)), value))
    return {'files': dex_files, 'matching_string_count': len(strings), 'strings': ranked[:160],
            'matching_class_count': len(classes), 'classes': sorted(classes)[:160],
            'matching_method_count': len(methods), 'methods': sorted(methods)[:240]}


def signature(apksigner: str, path: Path) -> dict:
    process = subprocess.run([apksigner, 'verify', '--verbose', '--print-certs', str(path)],
                             text=True, capture_output=True, timeout=120, check=False)
    output = process.stdout + '\n' + process.stderr
    digests = sorted(set(re.findall(r'certificate SHA-256 digest:\s*([0-9a-f]{64})', output, re.I)))
    return {'verified': process.returncode == 0 and bool(digests),
            'signer_sha256': [value.lower() for value in digests]}


def inspect(path: Path, decoded: Path, apksigner: str) -> dict:
    from androguard.core.apk import APK
    from loguru import logger
    logger.remove()
    check_asset(path)
    apk = APK(str(path))
    if not apk.is_valid_APK():
        raise ValueError('APK manifest is invalid')
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('APK contains duplicate archive entries')
        native = sorted(name for name in names if name.startswith('lib/') and name.endswith('.so'))
    resources = resource_inventory(decoded)
    return {
        'source': {'release_tag': 'King-Patcher', 'asset_id': 723503683,
                   'name': ASSET_NAME, 'size': ASSET_SIZE, 'sha256': ASSET_SHA256},
        'scope': 'Read-only static inventory; no APK modified, installed or published.',
        'package': apk.get_package(), 'version_name': apk.get_androidversion_name(),
        'version_code': apk.get_androidversion_code(), 'min_sdk': apk.get_min_sdk_version(),
        'target_sdk': apk.get_target_sdk_version(), 'app_label': apk.get_app_name(),
        'signature': signature(apksigner, path),
        'activity_count': len(apk.get_activities()), 'service_count': len(apk.get_services()),
        'activities': sorted(apk.get_activities())[:100],
        'native_libraries': native[:80], 'dex': dex_inventory(path),
        'resources': resources,
        'screen_references': smali_references(decoded, resources.get('screen_candidates', [])),
        'warning': 'Static identifiers alone do not establish that a feature works or is safely hookable.',
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('decoded', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--apksigner', required=True)
    args = parser.parse_args()
    report = inspect(args.apk, args.decoded, args.apksigner)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'package': report['package'], 'version': report['version_name'],
                      'code': report['version_code'], 'signature': report['signature'],
                      'dex_files': report['dex']['files'], 'resources': report['resources']['available'],
                      'screen_candidates': len(report['resources'].get('screen_candidates', [])),
                      'screen_references': report['screen_references']['reference_count']
                          if 'reference_count' in report['screen_references'] else 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
