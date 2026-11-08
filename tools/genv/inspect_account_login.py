#!/usr/bin/env python3
"""Inspect the pinned GenV base for account-related implementation evidence.

Read-only: never run/install the app or contact Google/GenV. We emit only counts
of allowlisted SDK/word indicators, bounded code identifiers and presence flags,
not APK bytes, arbitrary strings, account data, URLs, keys or tokens. The release
base has no native Flutter AOT library; negative matches do NOT prove that a
feature is absent from the full application or from its server.
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

from inspect_genv import ASSET_SHA256, DEX_NAME, PACKAGE, check_asset

# Explicit, narrowly bounded labels. A hit is a static indicator, not proof
# that a login path is reachable, configured, or associated with GenV's UI.
METHOD_LABELS = {
    'signInWithEmailAndPassword': 'email_password_signin_sdk_label',
    'createUserWithEmailAndPassword': 'email_password_signup_sdk_label',
    'sendPasswordResetEmail': 'password_reset_sdk_label',
    'confirmPasswordReset': 'password_reset_confirm_sdk_label',
    'verifyPasswordResetCode': 'password_reset_verify_sdk_label',
    'updatePassword': 'update_password_sdk_label',
    'linkWithCredential': 'link_credential_sdk_label',
    'reauthenticateWithCredential': 'reauthenticate_sdk_label',
}
WORD_LABELS = {
    'username': 'username_word',
    'password': 'password_word',
    'login': 'login_word',
    'sign in': 'sign_in_words',
    'sign up': 'sign_up_words',
    'signup': 'signup_word',
    'forgot password': 'forgot_password_words',
    'reset password': 'reset_password_words',
    'set password': 'set_password_words',
}
RESOURCE_NAMES = {
    'username', 'password', 'login', 'sign_in', 'sign_up', 'signup',
    'forgot_password', 'reset_password', 'set_password',
}
# A DEX method/field descriptor, not a free-form APK operand. Keeping the
# grammar narrow prevents a URL or arbitrary string in parentheses from being
# emitted as though it were a method identifier.
DEX_CLASS = r'L[A-Za-z0-9_$/-]+;'
DEX_TYPE = rf'(?:\[*[ZBCSIJFD]|\[*{DEX_CLASS})'
DEX_MEMBER = r'[A-Za-z0-9_$<>-]+'
VALID_SITE = re.compile(rf'{DEX_CLASS}->{DEX_MEMBER}\((?:{DEX_TYPE})*\)(?:V|{DEX_TYPE})\Z')
VALID_FIELD = re.compile(rf'{DEX_CLASS}->{DEX_MEMBER}{DEX_TYPE}\Z')
ACCOUNT_SITE = 'Lf6/m;->a(Lorg/json/JSONObject;)Lf6/m;'
CONTEXT_WORDS = frozenset({
    # Fixed public Flutter text-input configuration and autofill keys/hints.
    'inputaction', 'fields', 'contentcommitmimetypes', 'obscuretext', 'autocorrect',
    'enablesuggestions', 'enableimepersonalizedlearning', 'enabledeltamodel',
    'textcapitalization', 'inputtype', 'actionlabel', 'autofill', 'uniqueidentifier',
    'hints', 'hinttext', 'editingvalue', 'newpassword', 'newusername', 'onetimecode',
    'creditcardnumber', 'addresscity', 'email', 'username', 'password',
    # Other fixed context terms, not arbitrary APK strings.
    'host', 'port', 'proxy', 'scheme', 'http', 'https', 'type', 'auth', 'user',
    'domain', 'enabled', 'proxyhost', 'proxyport', 'proxyusername', 'proxypassword',
    'server', 'login', 'sign in', 'sign up',
})


def safe_trace_reference(operand: str) -> str | None:
    references = re.findall(r'L[A-Za-z0-9_$/-]+;->[^,]+', operand)
    if not references:
        return None
    value = ''.join(references[-1].split())
    if len(value) > 260:
        return None
    return value if VALID_SITE.fullmatch(value) or VALID_FIELD.fullmatch(value) else None


def context_label(operand: str) -> str | None:
    pieces = operand.split(',', 1)
    if len(pieces) != 2:
        return None
    text = pieces[1].strip()
    if len(text) < 2 or text[0] != '"' or text[-1] != '"':
        return None
    word = text[1:-1].casefold()
    return word if word in CONTEXT_WORDS else None


def label_value(value: str) -> str | None:
    """A fixed label only; never return the input or a substring of it."""
    if value in METHOD_LABELS:
        return METHOD_LABELS[value]
    # Flutter Pigeon method channels include an SDK prefix and method name.
    prefix = 'dev.flutter.pigeon.firebase_auth_platform_interface.'
    if value.startswith(prefix):
        method = value.rsplit('.', 1)[-1]
        return METHOD_LABELS.get(method)
    return WORD_LABELS.get(value.casefold())


def resource_evidence(apk) -> list[str]:
    from lxml import etree
    found = set()
    arsc = apk.get_android_resources()
    if arsc:
        for package in arsc.get_packages_names():
            xml = arsc.get_string_resources(package)
            if not xml:
                continue
            for node in etree.fromstring(xml).iter('string'):
                name = node.get('name', '')
                if name in RESOURCE_NAMES:
                    found.add(name)
    return sorted(found)


def inspect(path: Path) -> dict:
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    logger.remove()
    check_asset(path)
    apk = APK(str(path))
    if not apk.is_valid_APK() or apk.get_package() != PACKAGE or apk.get_androidversion_name() != '3.7.2' or apk.get_androidversion_code() != '163':
        raise ValueError('Unexpected GenV target')
    resources = resource_evidence(apk)
    dex_counts = Counter()
    sites: dict[str, list[str]] = defaultdict(list)
    class_counts = Counter()
    asset_counts = Counter()
    site_trace = None
    site_callers = []
    dex_files = []
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = {i.filename for i in infos}
        if len(names) != len(infos):
            raise ValueError('Duplicate APK entries')
        native_count = sum(1 for name in names if name.startswith('lib/') and name.endswith('.so'))
        flutter_assets = any(name.startswith('assets/flutter_assets/') for name in names)
        aot_present = any(name.startswith('lib/') and name.endswith('/libapp.so') for name in names)
        kernel_present = any(name.startswith('assets/flutter_assets/') and name.endswith('/kernel_blob.bin') for name in names)
        # Search only text and snapshot-style Flutter asset files. Emit counts
        # for fixed byte sequences, never an asset's actual text or filename.
        byte_needles = {label: word.encode('utf-8').lower() for word, label in WORD_LABELS.items()}
        byte_needles.update({label: word.encode('utf-8').lower() for word, label in METHOD_LABELS.items()})
        scanned_asset_files = 0
        total_scanned_asset_bytes = 0
        for info in infos:
            name = info.filename
            if not name.startswith('assets/flutter_assets/'):
                continue
            if not (name.lower().endswith(('.json', '.txt', '.html', '.js', '.yaml', '.bin'))
                    or name.endswith(('/vm_snapshot_data', '/isolate_snapshot_data', '/kernel_blob.bin'))):
                continue
            if info.file_size > 32 * 1024 * 1024 or total_scanned_asset_bytes + info.file_size > 96 * 1024 * 1024:
                raise ValueError('Flutter asset scan size exceeded')
            raw = archive.read(info).lower()
            scanned_asset_files += 1
            total_scanned_asset_bytes += len(raw)
            for label, needle in byte_needles.items():
                asset_counts[label] += raw.count(needle)
        for info in infos:
            if not DEX_NAME.fullmatch(info.filename):
                continue
            if not 0 < info.file_size <= 128 * 1024 * 1024:
                raise ValueError('Unexpected DEX size')
            dex_files.append(info.filename)
            dex = DEX(archive.read(info))
            for cls in dex.get_classes():
                cls_name = cls.get_name()
                if cls_name.startswith('Lcom/google/firebase/auth/'):
                    class_counts['firebase_auth_named_classes'] += 1
                if cls_name.startswith(('Lio/flutter/plugins/firebase/auth/',
                                        'Lio/flutter/plugins/firebaseauth/')):
                    class_counts['flutter_firebase_auth_named_classes'] += 1
                if cls_name.startswith('Lcom/google/android/gms/auth/api/signin/'):
                    class_counts['google_signin_named_classes'] += 1
                for method in cls.get_methods():
                    if method.get_code() is None:
                        continue
                    method_id = cls_name + '->' + method.get_name() + ''.join(method.get_descriptor().split())
                    if not VALID_SITE.fullmatch(method_id):
                        continue
                    trace_events = []
                    site_invocations = []
                    known_words = []
                    instruction_count = 0
                    for index, ins in enumerate(method.get_instructions()):
                        instruction_count += 1
                        op = ins.get_name()
                        operand = ins.get_output()
                        if op.startswith(('invoke-', 'iget', 'iput', 'sget', 'sput')):
                            reference = safe_trace_reference(operand)
                            if reference:
                                if reference == ACCOUNT_SITE and op.startswith('invoke-') and len(site_invocations) < 12:
                                    site_invocations.append({'index': index, 'opcode': op, 'reference': reference})
                                if len(trace_events) < 100:
                                    trace_events.append({'index': index, 'opcode': op, 'reference': reference})
                        elif op.startswith('const-string'):
                            word = context_label(operand)
                            if word:
                                if method_id == ACCOUNT_SITE and len(known_words) < 100:
                                    known_words.append({'index': index, 'known_word': word})
                                if len(trace_events) < 100:
                                    trace_events.append({'index': index, 'opcode': op, 'known_word': word})
                        label = None
                        if op.startswith('const-string'):
                            pieces = operand.split(',', 1)
                            if len(pieces) == 2:
                                text = pieces[1].strip()
                                if len(text) >= 2 and text[0] == text[-1] == '"':
                                    label = label_value(text[1:-1])
                        elif op.startswith('invoke-') and 'Lcom/google/firebase/auth/' in operand:
                            match = re.search(r'->([A-Za-z0-9_$]+)\(', operand)
                            if match and match.group(1) in METHOD_LABELS:
                                label = METHOD_LABELS[match.group(1)] + '_call'
                        if label:
                            dex_counts[label] += 1
                            if method_id not in sites[label] and len(sites[label]) < 12:
                                sites[label].append(method_id)
                    if method_id == ACCOUNT_SITE:
                        site_trace = {'method': method_id, 'flags': method.get_access_flags_string(),
                                      'instruction_count': instruction_count, 'known_words': known_words,
                                      'events': trace_events}
                    elif site_invocations and len(site_callers) < 12:
                        site_callers.append({'method': method_id, 'instruction_count': instruction_count,
                                             'site_invocations': site_invocations, 'events': trace_events})
            del dex
            gc.collect()
    check_asset(path)
    return {
        'scope': 'SHA-pinned release base only; read-only, no GenV execution, accounts or Google/GenV requests',
        'package': PACKAGE, 'version': '3.7.2', 'version_code': 163, 'base_sha256': ASSET_SHA256,
        'files': {
            'dex_files': dex_files, 'native_library_count': native_count,
            'flutter_assets_present': flutter_assets,
            'flutter_libapp_so_in_base': aot_present,
            'flutter_kernel_blob_in_base': kernel_present,
            'flutter_text_or_snapshot_assets_scanned': scanned_asset_files,
            'scanned_asset_bytes': total_scanned_asset_bytes,
        },
        'named_sdk_class_counts': {name: class_counts[name] for name in
                                   ('firebase_auth_named_classes', 'flutter_firebase_auth_named_classes', 'google_signin_named_classes')},
        'fixed_dex_indicator_counts': dict(sorted(dex_counts.items())),
        'indicator_method_sites': dict(sorted(sites.items())),
        'reviewed_username_password_site': site_trace,
        'reviewed_site_callers': site_callers,
        'fixed_flutter_asset_indicator_counts': {k: v for k, v in sorted(asset_counts.items()) if v},
        'matching_android_string_resource_names': resources,
        'interpretation_limits': [
            'SDK and generic word matches alone do not establish a usable login, signup, reset, or account-linking feature',
            'Named classes and method names can be obfuscated; a zero count is not proof of absence',
            'Flutter AOT code and configuration splits required by the release app are not present in the inspected base',
            'Backend registration, password reset, website/app account sharing and Google account linking are unknown',
            'No real app, account, password, server request or Google sign-in was tested',
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
    print('Inspected fixed account indicators in the base; no APK, account data or arbitrary strings exported.')


if __name__ == '__main__':
    main()
