#!/usr/bin/env python3
"""Inspect the exact uploaded Instant Translate APK without running or modifying it.

Only sanitized metadata, feature-name evidence and allowlisted service hostnames
are recorded. URLs, tokens, user data and APK bytes are never included in reports.
A name or library indicator does not establish runtime behavior or a working fix.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import re
import subprocess
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

ASSET_ID = 692278800
FILENAME = 'Instant.Translate-v7.5.00300-com.spaceship.screen.textcopy.apk'
EXPECTED_SIZE = 49517706
EXPECTED_SHA256 = 'f341a1b174bda7b5d1c95cb2fc84da238228a116844069ee962220acaf1e4e4c'
EXPECTED_PACKAGE = 'com.spaceship.screen.textcopy'
DEX_NAME = re.compile(r'classes(?:[2-9]|[1-9][0-9]+)?\.dex\Z')
CERT_SHA256 = re.compile(r'certificate SHA-256 digest:\s*([0-9a-f]{64})', re.I)
CERT_SHA1 = re.compile(r'certificate SHA-1 digest:\s*([0-9a-f]{40})', re.I)
SENSITIVE = re.compile(r'(?i)(https?://|www\.|@|token|secret|password|credential|api.?key|private.?key|bearer|[A-Za-z0-9_+/=-]{48,})')
CATEGORIES = {
    'translation': re.compile(r'translat(?:e|es|ed|or|ion|ing|ions|ors)?|translator', re.I),
    'recognition': re.compile(r'(?<![a-z])ocr(?![a-z])|text.?recognition|text.?recognizer|image.?recognition', re.I),
    'network_errors': re.compile(r'network.{0,20}(?:fail|error|disconnect)|(?:fail|error).{0,20}(?:network|connection)|connection.{0,15}(?:error|fail)', re.I),
    'translation_errors': re.compile(r'(?:translat|engine).{0,30}(?:fail|error|unavailable|unsupported)|(?:fail|error).{0,30}translat', re.I),
    'offline': re.compile(r'offline|on.?device|download.?model', re.I),
}
# Only public, known service domains are reported; all other hosts and every path/query are omitted.
KNOWN_HOSTS = frozenset({
    'translate.googleapis.com', 'translation.googleapis.com', 'translate.google.com',
    'clients5.google.com', 'www.googleapis.com', 'api.cognitive.microsofttranslator.com',
    'api-free.deepl.com', 'api.deepl.com', 'api.openai.com', 'api.mymemory.translated.net',
    'translate.yandex.net', 'jiiqii.com', 'www.jiiqii.com',
})
LIBRARY_PREFIXES = {
    'google_mlkit_translation': ('Lcom/google/mlkit/nl/translate/',),
    'google_mlkit_text_recognition': ('Lcom/google/mlkit/vision/text/',),
    'firebase_remote_config': ('Lcom/google/firebase/remoteconfig/',),
    'google_play_services': ('Lcom/google/android/gms/',),
    'google_mobile_ads': ('Lcom/google/android/gms/ads/',),
    'android_billing': ('Lcom/android/billingclient/',),
    'okhttp': ('Lokhttp3/',),
    'retrofit': ('Lretrofit2/',),
    'flutter': ('Lio/flutter/',),
    'react_native': ('Lcom/facebook/react/',),
}


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify_asset(path: Path) -> None:
    if path.stat().st_size != EXPECTED_SIZE or digest_file(path) != EXPECTED_SHA256:
        raise ValueError('APK does not match the pinned pre-release asset')
    if not zipfile.is_zipfile(path):
        raise ValueError('Uploaded asset is not an APK/ZIP archive')


def safe_sample(value: str) -> bool:
    return bool(value and len(value) <= 120 and value.isprintable() and not SENSITIVE.search(value))


def allowed_host(value: str) -> str | None:
    """Return only an allowlisted hostname, never a URL, path, query or credentials."""
    if not isinstance(value, str) or not value.startswith(('https://', 'http://')):
        return None
    try:
        host = (urlsplit(value).hostname or '').lower()
    except ValueError:
        return None
    return host if host in KNOWN_HOSTS else None


def signature(apksigner: str, path: Path, min_sdk: str) -> dict:
    if not min_sdk.isdigit() or not 1 <= int(min_sdk) <= 100:
        raise ValueError('APK has an invalid minimum SDK')
    result = subprocess.run([apksigner, 'verify', '--verbose', '--print-certs', '--min-sdk-version', min_sdk, str(path)],
                            check=False, capture_output=True, text=True, timeout=180)
    text = result.stdout + '\n' + result.stderr
    sha256 = sorted({v.lower() for v in CERT_SHA256.findall(text)})
    sha1 = sorted({v.lower() for v in CERT_SHA1.findall(text)})
    return {'verified': result.returncode == 0 and bool(sha256), 'signer_sha256': sha256, 'signer_sha1': sha1}


def resources(apk) -> dict:
    """Default-locale matching resource names/short strings, never URLs/secrets."""
    from lxml import etree

    found: dict[str, list[dict]] = {name: [] for name in CATEGORIES}
    resource_table = apk.get_android_resources()
    if resource_table is None:
        return {'default_locale_matches': found, 'available': False}
    packages = resource_table.get_packages_names()
    for package in packages:
        xml = resource_table.get_string_resources(package)
        if not xml:
            continue
        root = etree.fromstring(xml)
        for item in root.iter('string'):
            name = item.get('name', '')
            text = ''.join(item.itertext()).strip()
            for category, pattern in CATEGORIES.items():
                if len(found[category]) >= 40:
                    continue
                if pattern.search(name) or pattern.search(text):
                    if safe_sample(name):
                        entry = {'name': name}
                        if safe_sample(text):
                            entry['text'] = text
                        found[category].append(entry)
    return {'default_locale_matches': found, 'available': True}


def dex_inventory(path: Path, apk_package: str) -> dict:
    from androguard.core.dex import DEX

    app_root = 'L' + '/'.join(apk_package.split('.')[:2]) + '/'
    counts = Counter()
    libraries = Counter()
    domains = Counter()
    first_party_classes = defaultdict(set)
    first_party_methods = defaultdict(set)
    strings = defaultdict(set)
    dex_files = []
    total = 0
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if len({info.filename for info in infos}) != len(infos):
            raise ValueError('Duplicate ZIP entries in APK')
        for info in infos:
            if not DEX_NAME.fullmatch(info.filename):
                continue
            total += info.file_size
            if not 0 < info.file_size <= 100 * 1024 * 1024 or total > 400 * 1024 * 1024:
                raise ValueError('Unexpected DEX file sizes')
            dex_files.append({'name': info.filename, 'bytes': info.file_size})
            dex = DEX(archive.read(info))
            for value in dex.get_strings():
                if not isinstance(value, str):
                    continue
                host = allowed_host(value)
                if host:
                    domains[host] += 1
                for category, pattern in CATEGORIES.items():
                    if pattern.search(value):
                        counts[category] += 1
                        if category in ('translation_errors', 'network_errors') and safe_sample(value):
                            strings[category].add(value)
            for cls in dex.get_classes():
                name = cls.get_name()
                for library, prefixes in LIBRARY_PREFIXES.items():
                    if name.startswith(prefixes):
                        libraries[library] += 1
                if not name.startswith(app_root):
                    continue
                for category, pattern in CATEGORIES.items():
                    if pattern.search(name):
                        first_party_classes[category].add(name)
                for method in cls.get_methods():
                    method_name = method.get_name()
                    for category, pattern in CATEGORIES.items():
                        if pattern.search(name) or pattern.search(method_name):
                            descriptor = ''.join(method.get_descriptor().split())
                            first_party_methods[category].add(f'{name}->{method_name}{descriptor}')
            del dex
            gc.collect()
    return {
        'dex_files': dex_files,
        'first_party_prefix': app_root,
        'feature_string_counts': dict(sorted(counts.items())),
        'error_string_samples': {key: sorted(values)[:30] for key, values in sorted(strings.items())},
        'first_party_feature_classes': {key: sorted(values)[:100] for key, values in sorted(first_party_classes.items())},
        'first_party_feature_methods': {key: sorted(values)[:150] for key, values in sorted(first_party_methods.items())},
        'known_libraries_class_counts': dict(sorted(libraries.items())),
        'allowlisted_service_hosts_found_as_strings': dict(sorted(domains.items())),
        'note': 'Names, libraries and strings are indicators only, not proof of usage or runtime behavior.',
    }


def inspect(path: Path, apksigner: str) -> dict:
    from androguard.core.apk import APK
    from loguru import logger
    logger.remove()
    verify_asset(path)
    apk = APK(str(path))
    if not apk.is_valid_APK() or apk.get_package() != EXPECTED_PACKAGE:
        raise ValueError('Unexpected APK identity')
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(set(names)) != len(names):
            raise ValueError('Duplicate ZIP entries in APK')
        native_abis = sorted({name.split('/')[1] for name in names if name.startswith('lib/') and name.endswith('.so') and name.count('/') >= 2})
        indicators = {
            'flutter_native': any(name.endswith('/libflutter.so') for name in names),
            'react_native_bundle': any(name.endswith('assets/index.android.bundle') for name in names),
            'unity_native': any(name.endswith('/libunity.so') or name.endswith('/libil2cpp.so') for name in names),
            'ml_model_assets_count': sum(1 for name in names if name.startswith('assets/') and name.lower().endswith(('.tflite', '.onnx', '.pb', '.bin', '.model'))),
        }
    component_keywords = re.compile(r'translat|ocr|capture|projection|overlay|accessibility|textcopy|screen|bubble', re.I)
    components = {
        'application': apk.get_attribute_value('application', 'name'),
        'main_activity': apk.get_main_activity(),
        'activities': [name for name in apk.get_activities() if component_keywords.search(name)][:80],
        'services': [name for name in apk.get_services() if component_keywords.search(name)][:80],
        'receivers': [name for name in apk.get_receivers() if component_keywords.search(name)][:50],
        'providers': [name for name in apk.get_providers() if component_keywords.search(name)][:50],
    }
    permissions = sorted(p for p in apk.get_permissions() if re.search(r'INTERNET|NETWORK_STATE|SYSTEM_ALERT_WINDOW|FOREGROUND_SERVICE|MEDIA_PROJECTION|RECORD_AUDIO|BIND_ACCESSIBILITY_SERVICE', p))
    min_sdk = str(apk.get_min_sdk_version() or '')
    return {
        'scope': 'Static inspection of the supplied APK only; no app launch, external requests, patch, or credentials.',
        'source': {'release_tag': 'Instant-translate', 'asset_id': ASSET_ID, 'filename': path.name, 'bytes': EXPECTED_SIZE, 'sha256': EXPECTED_SHA256},
        'identity': {'package': apk.get_package(), 'label': apk.get_app_name(), 'version_name': apk.get_androidversion_name(),
                     'version_code': apk.get_androidversion_code(), 'min_sdk': min_sdk, 'target_sdk': apk.get_target_sdk_version(),
                     'manifest_split': apk.get_attribute_value('manifest', 'split')},
        'signature': signature(apksigner, path, min_sdk),
        'native_abis': native_abis, 'framework_indicators': indicators,
        'relevant_permissions': permissions, 'relevant_components': components,
        'resources': resources(apk), 'dex': dex_inventory(path, apk.get_package()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('--apksigner', required=True)
    args = parser.parse_args()
    report = inspect(args.apk, args.apksigner)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'identity': report['identity'], 'signature': report['signature'], 'native_abis': report['native_abis'],
                      'frameworks': report['framework_indicators'], 'dex_files': report['dex']['dex_files'],
                      'known_libraries': report['dex']['known_libraries_class_counts'],
                      'allowlisted_hosts': report['dex']['allowlisted_service_hosts_found_as_strings']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
