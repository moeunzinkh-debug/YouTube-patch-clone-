#!/usr/bin/env python3
"""Read-only, privacy-bounded feasibility check for a GenV browser sign-in.

Only fixed indicator counts, manifest component identifiers and scheme classes
are reported. Raw URLs, OAuth client IDs, arbitrary strings, code, tokens,
accounts and APK bytes are never printed or saved. This does not contact Google,
GenV, Firebase or a user account and cannot establish server configuration.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from inspect_genv import ANDROID, ASSET_SHA256, DEX_NAME, PACKAGE, check_asset

VIEW = 'android.intent.action.VIEW'
BROWSABLE = 'android.intent.category.BROWSABLE'
CLIENT_ID = re.compile(r'[A-Za-z0-9-]+\.apps\.googleusercontent\.com\Z')
IDENTIFIER = re.compile(r'[A-Za-z0-9_.$]+\Z')

# Known public SDK labels, not arbitrary APK values.
EXACT_INDICATORS = {
    'plugins.flutter.io/google_sign_in': 'flutter_google_signin_channel',
    'signIn': 'method_sign_in',
    'signInSilently': 'method_sign_in_silently',
    'getTokens': 'method_get_tokens',
    'idToken': 'field_id_token',
    'accessToken': 'field_access_token',
    'serverAuthCode': 'field_server_auth_code',
    'serverClientId': 'field_server_client_id',
    'clientId': 'field_client_id',
    'oauth2redirect': 'oauth2_redirect_label',
    'https://accounts.google.com/o/oauth2/v2/auth': 'google_oauth_endpoint',
}


def indicator(value: str) -> str | None:
    if value in EXACT_INDICATORS:
        return EXACT_INDICATORS[value]
    if value.startswith('dev.flutter.pigeon.google_sign_in_android.'):
        return 'flutter_google_signin_pigeon_channel'
    return None


def scheme_type(scheme: str, client_ids: set[str]) -> str:
    if not scheme:
        return 'none'
    if scheme in ('http', 'https'):
        return scheme
    if scheme.startswith('com.googleusercontent.apps.'):
        reversed_ids = {'com.googleusercontent.apps.' + value.removesuffix('.apps.googleusercontent.com')
                        for value in client_ids if CLIENT_ID.fullmatch(value)}
        return 'google_reversed_known_client' if scheme in reversed_ids else 'google_reversed_other'
    if scheme.startswith('@'):
        return 'resource_reference'
    return 'other_custom_scheme'


def summarize_browsable(root, client_ids: set[str]) -> list[dict]:
    application = root.find('application')
    if application is None:
        raise ValueError('Application element missing')
    results = []
    for kind in ('activity', 'activity-alias'):
        for component in application.findall(kind):
            name = component.get(ANDROID + 'name', '')
            if not IDENTIFIER.fullmatch(name) or len(name) > 200:
                continue
            for item in component.findall('intent-filter'):
                actions = {x.get(ANDROID + 'name', '') for x in item.findall('action')}
                categories = {x.get(ANDROID + 'name', '') for x in item.findall('category')}
                if VIEW not in actions or BROWSABLE not in categories:
                    continue
                data = item.findall('data')
                scheme_types = sorted({scheme_type(x.get(ANDROID + 'scheme', ''), client_ids)
                                       for x in data} or {'none'})
                # Never emit host, path, resource value, or URI: only a bounded
                # semantic hint, which is not proof of any OAuth registration.
                path_hint = any(re.search(r'oauth|callback|signin|sign-in|__/auth',
                                          (x.get(ANDROID + 'path', '') + '/' +
                                           x.get(ANDROID + 'pathPrefix', '') + '/' +
                                           x.get(ANDROID + 'pathPattern', '')), re.I)
                                for x in data)
                results.append({'component': name, 'kind': kind,
                                'exported': component.get(ANDROID + 'exported', 'implicit'),
                                'auto_verify': item.get(ANDROID + 'autoVerify', 'false'),
                                'scheme_types': scheme_types,
                                'oauth_like_path_present': path_hint})
    return results


def resource_values(apk) -> tuple[bool, set[str]]:
    from lxml import etree
    arsc = apk.get_android_resources()
    if not arsc:
        return False, set()
    present = False
    client_ids = set()
    for package in arsc.get_packages_names():
        xml = arsc.get_string_resources(package)
        if not xml:
            continue
        for node in etree.fromstring(xml).iter('string'):
            if node.get('name', '') == 'default_web_client_id':
                present = True
                text = ''.join(node.itertext()).strip()
                if CLIENT_ID.fullmatch(text):
                    client_ids.add(text)
    return present, client_ids


def inspect(path: Path) -> dict:
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    logger.remove()
    check_asset(path)
    apk = APK(str(path))
    if not apk.is_valid_APK() or apk.get_package() != PACKAGE or apk.get_androidversion_name() != '3.7.2' or apk.get_androidversion_code() != '163':
        raise ValueError('Unexpected GenV target')
    root = apk.get_android_manifest_xml()
    present, client_ids = resource_values(apk)
    counts = Counter()
    sites: dict[str, list[str]] = defaultdict(list)
    dex_files = []
    libraries = []
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if len({i.filename for i in infos}) != len(infos):
            raise ValueError('Duplicate APK entries')
        libraries = [x.filename for x in infos if x.filename.startswith('lib/') and x.filename.endswith('/libapp.so')]
        for info in infos:
            if not DEX_NAME.fullmatch(info.filename):
                continue
            if not 0 < info.file_size <= 128 * 1024 * 1024:
                raise ValueError('Unexpected DEX size')
            dex_files.append(info.filename)
            dex = DEX(archive.read(info))
            for cls in dex.get_classes():
                name = cls.get_name()
                if name not in {'Lv6/a;', 'Lv6/b;'}:
                    continue
                for method in cls.get_methods():
                    if method.get_code() is None:
                        continue
                    method_id = name + '->' + method.get_name() + ''.join(method.get_descriptor().split())
                    for ins in method.get_instructions():
                        if not ins.get_name().startswith('const-string'):
                            continue
                        operand = ins.get_output().split(',', 1)
                        if len(operand) != 2:
                            continue
                        value = operand[1].strip()
                        if len(value) < 2 or value[0] != '"' or value[-1] != '"':
                            continue
                        label = indicator(value[1:-1])
                        if label:
                            counts[label] += 1
                            if len(sites[label]) < 15 and method_id not in sites[label]:
                                sites[label].append(method_id)
            del dex
            gc.collect()
    check_asset(path)
    return {
        'scope': 'SHA-pinned released GenV base only; read-only, no execution, accounts or network requests',
        'package': PACKAGE, 'version': '3.7.2', 'version_code': 163, 'input_sha256': ASSET_SHA256,
        'default_web_client_id_resource_present': present,
        'default_web_client_id_has_google_client_id_shape': bool(client_ids),
        'client_id_value_and_type': 'not emitted; actual OAuth client configuration unknown',
        'browsable_view_intent_filters': summarize_browsable(root, client_ids),
        'fixed_google_signin_labels_in_reviewed_bridge_classes': dict(sorted(counts.items())),
        'label_method_sites': dict(sorted(sites.items())),
        'reviewed_bridge_classes': ['Lv6/a;', 'Lv6/b;'], 'dex_files': dex_files,
        'flutter_native_libapp_in_base': bool(libraries),
        'constraints': [
            'Base has no required configuration/native splits; Flutter AOT app and full app behavior were not analyzed',
            'Manifest filters do not establish Google authorized redirect URIs or app-link ownership',
            'The server exchange, accepted token audience and full login behavior are unknown',
            'No actual browser login, Google account, network or Huawei device was tested',
        ],
        'ci_run': f"https://github.com/{os.environ.get('GITHUB_REPOSITORY','')}/actions/runs/{os.environ.get('GITHUB_RUN_ID','')}",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    report = inspect(args.apk)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('Inspected only fixed browser/Google-sign-in indicators; no credentials, URLs, IDs or APK exported.')


if __name__ == '__main__':
    main()
