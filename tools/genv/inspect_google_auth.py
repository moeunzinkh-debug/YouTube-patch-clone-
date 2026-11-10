#!/usr/bin/env python3
"""Read-only, privacy-bounded inspection of GenV's Google sign-in integration.

The report contains structural identifiers, allowlisted GMS routing literals,
counts and signer fingerprints. It never contains APK bytes, OAuth IDs, tokens,
URLs, passwords, user accounts, arbitrary string values, or network traffic.
"""
from __future__ import annotations
import argparse
import gc
import json
import re
import subprocess
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from inspect_genv import ANDROID, DEX_NAME, PACKAGE, ASSET_SHA256, check_asset

LIBRARIES = {
    'google_signin': ('Lcom/google/android/gms/auth/api/signin/',),
    'google_identity': ('Lcom/google/android/gms/auth/api/identity/', 'Lcom/google/android/libraries/identity/googleid/'),
    'firebase_auth': ('Lcom/google/firebase/auth/',),
    'androidx_credentials': ('Landroidx/credentials/',),
    'react_native': ('Lcom/facebook/react/', 'Lexpo/modules/'),
    'react_native_google_signin': ('Lcom/reactnativegooglesignin/', 'Lco/apptailor/googlesignin/'),
    'flutter': ('Lio/flutter/',),
    'flutter_google_signin': ('Lio/flutter/plugins/googlesignin/',),
    'play_integrity': ('Lcom/google/android/play/core/integrity/',),
    'firebase_app_check': ('Lcom/google/firebase/appcheck/',),
    'google_services_common': ('Lcom/google/android/gms/common/',),
}
REFERENCE_PREFIXES = (
    'Lcom/google/android/gms/auth/api/signin/', 'Lcom/google/android/gms/auth/api/identity/',
    'Lcom/google/android/libraries/identity/googleid/', 'Lcom/google/firebase/auth/',
    'Landroidx/credentials/', 'Lcom/google/android/gms/common/GoogleApiAvailability',
    'Lcom/google/android/play/core/integrity/', 'Lcom/google/firebase/appcheck/',
)
ROUTE = re.compile(r'(?:com\.google(?:\.android\.(?:gms|gsf|c2dm|googleapps|gtalkservice)(?:\.[A-Za-z0-9_$]+)*)?|content://com\.google\.android\.(?:gms|gsf)(?:\.[A-Za-z0-9_$]+)*)\Z')
IDENTIFIER = re.compile(r'[A-Za-z0-9_$/;()<>.$\[\]-]+\Z')
BRIDGE = re.compile(r'googlesignin|google.?sign.?in|firebaseauth|credentials?manager|authsession', re.I)
JS_INDICATORS = {
    'google_signin': b'googlesignin', 'native_google_signin': b'rngooglesignin',
    'expo_auth_session': b'expo-auth-session', 'firebase_auth': b'firebaseauth',
    'google_services_package': b'com.google.android.gms', 'revanced_services_package': b'app.revanced.android.gms',
    'google_button_label': b'continue with google', 'generic_error_label': b'something went wrong',
    'integrity_indicator': b'playintegrity', 'app_check_indicator': b'appcheck',
}
RESOURCE_NAMES = {'default_web_client_id', 'google_app_id', 'gcm_defaultSenderId', 'google_api_key'}


def route_literal(value: str) -> bool:
    """Permit only known package/action/provider identifiers, never parameters."""
    return 1 <= len(value) <= 180 and bool(ROUTE.fullmatch(value))


def extract_route(operand: str) -> str | None:
    if ',' not in operand: return None
    value = operand.split(',', 1)[1].strip()
    if len(value) < 2 or value[0] != '"' or value[-1] != '"': return None
    value = value[1:-1]
    return value if route_literal(value) else None


def identifier(value: str) -> bool:
    return 1 <= len(value) <= 260 and bool(IDENTIFIER.fullmatch(value))


def signer(apksigner: str, path: Path) -> dict:
    result = subprocess.run([apksigner, 'verify', '--verbose', '--print-certs', '--min-sdk-version', '24', str(path)],
                            check=False, capture_output=True, text=True, timeout=120)
    text = result.stdout + '\n' + result.stderr
    sha1 = re.findall(r'^Signer #1 certificate SHA-1 digest:\s*([0-9a-f]{40})\s*$', text, re.I | re.M)
    sha256 = re.findall(r'^Signer #1 certificate SHA-256 digest:\s*([0-9a-f]{64})\s*$', text, re.I | re.M)
    return {'verified': result.returncode == 0, 'signer_1_sha1': sha1[0].lower() if sha1 else None,
            'signer_1_sha256': sha256[0].lower() if sha256 else None,
            'publisher_independently_authenticated': False}


def inspect(path: Path, apksigner: str) -> dict:
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    from lxml import etree
    logger.remove()
    check_asset(path)
    apk = APK(str(path))
    if not apk.is_valid_APK() or apk.get_package() != PACKAGE or apk.get_androidversion_name() != '3.7.2' or apk.get_androidversion_code() != '163':
        raise ValueError('Unexpected GenV target')
    manifest = apk.get_android_manifest_xml()
    queries = []
    for entry in manifest.findall('./queries/package'):
        name = entry.get(ANDROID + 'name', '')
        if name in {'com.google.android.gms', 'app.revanced.android.gms', 'com.android.vending'}:
            queries.append(name)
    perms = sorted(p for p in apk.get_permissions() if re.search(r'com\.google\.|GET_ACCOUNTS|USE_CREDENTIALS|AUTHENTICATE_ACCOUNTS|INTERNET', p))
    components = []
    for entry in manifest.findall('./application/activity') + manifest.findall('./application/provider') + manifest.findall('./application/service'):
        name = entry.get(ANDROID + 'name', '')
        if BRIDGE.search(name) and identifier(name):
            components.append({'kind': entry.tag, 'name': name, 'exported': entry.get(ANDROID + 'exported')})
    resources = {name: False for name in sorted(RESOURCE_NAMES)}
    arsc = apk.get_android_resources()
    if arsc:
        for package in arsc.get_packages_names():
            xml = arsc.get_string_resources(package)
            if xml:
                for node in etree.fromstring(xml).iter('string'):
                    name = node.get('name', '')
                    if name in resources: resources[name] = True

    libraries, route_count, ref_count = Counter(), Counter(), Counter()
    route_sites, auth_calls, bridge_classes = defaultdict(list), defaultdict(list), set()
    dex_files, framework_assets, js_evidence = [], {}, {}
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if len({i.filename for i in infos}) != len(infos): raise ValueError('Duplicate APK entries')
        names = {i.filename for i in infos}
        framework_assets = {'react_native_index_bundle': 'assets/index.android.bundle' in names,
                            'flutter_assets': any('flutter_assets/' in n for n in names),
                            'hermes_native': any(n.endswith('/libhermes.so') for n in names),
                            'flutter_native': any(n.endswith('/libflutter.so') for n in names)}
        # Only counts of fixed indicator bytes are retained, never arbitrary JS/Hermes content.
        for name in sorted(n for n in names if n == 'assets/index.android.bundle' or n.startswith('assets/updates/') and n.endswith(('.js', '.bundle', '.hbc'))):
            info = archive.getinfo(name)
            if not 0 < info.file_size <= 32 * 1024 * 1024: raise ValueError('Unexpected bundled JS size')
            content = archive.read(info).lower()
            js_evidence[name] = {label: content.count(needle) for label, needle in JS_INDICATORS.items()}
        for info in infos:
            if not DEX_NAME.fullmatch(info.filename): continue
            if not 0 < info.file_size <= 128 * 1024 * 1024: raise ValueError('Unexpected DEX size')
            dex_files.append(info.filename)
            dex = DEX(archive.read(info))
            for cls in dex.get_classes():
                cls_name = cls.get_name()
                for label, prefixes in LIBRARIES.items():
                    if cls_name.startswith(prefixes): libraries[label] += 1
                if BRIDGE.search(cls_name) and identifier(cls_name): bridge_classes.add(cls_name)
                for method in cls.get_methods():
                    if method.get_code() is None: continue
                    mid = cls_name + '->' + method.get_name() + ''.join(method.get_descriptor().split())
                    if not identifier(mid): continue
                    for index, ins in enumerate(method.get_instructions()):
                        op = ins.get_name()
                        if op.startswith('const-string'):
                            value = extract_route(ins.get_output())
                            if value is not None:
                                route_count[value] += 1
                                if len(route_sites[value]) < 80:
                                    route_sites[value].append({'method': mid, 'dex': info.filename, 'index': index, 'opcode': op})
                        elif op.startswith('invoke-'):
                            operand = ins.get_output()
                            for prefix in REFERENCE_PREFIXES:
                                if prefix in operand:
                                    ref_count[prefix] += 1
                                    ref = re.search(r'(L[A-Za-z0-9_$/-]+;->[A-Za-z0-9_$<>-]+\([^)]*\)[A-Za-z0-9_$/;\[\]-]+)', operand)
                                    target = ''.join(ref.group(1).split()) if ref else ''
                                    if identifier(target) and len(auth_calls[prefix]) < 60:
                                        auth_calls[prefix].append({'method': mid, 'target': target, 'dex': info.filename})
                                    break
            del dex
            gc.collect()
    check_asset(path)
    return {
        'scope': 'Read-only SHA-pinned inspection; no app install, execution, account access, requests or APK upload.',
        'package': PACKAGE, 'version_name': '3.7.2', 'version_code': 163, 'input_sha256': ASSET_SHA256,
        'signature': signer(apksigner, path),
        'manifest': {'package_visibility_queries': sorted(queries), 'relevant_permissions': perms,
                     'auth_related_components': components[:100], 'resource_names_present_only': resources},
        'framework_assets': framework_assets, 'fixed_js_indicator_counts': js_evidence,
        'dex_files': dex_files, 'library_class_counts': dict(sorted(libraries.items())),
        'auth_bridge_classes': sorted(bridge_classes)[:160],
        'gms_routing_string_counts': dict(sorted(route_count.items())),
        'gms_routing_sites': dict(sorted(route_sites.items())),
        'auth_api_reference_counts': dict(sorted(ref_count.items())),
        'auth_api_calls': dict(sorted(auth_calls.items())),
        'note': 'Static references do not prove a code path was used or identify the runtime error.'
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--apksigner', required=True)
    args = parser.parse_args()
    data = inspect(args.apk, args.apksigner)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + '\n')
    print('Inspected GenV Google authentication structure without exposing credentials or APK content.')

if __name__ == '__main__': main()
