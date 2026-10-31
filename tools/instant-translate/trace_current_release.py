#!/usr/bin/env python3
"""Read-only, sanitized static analysis of the pinned Instant Translate release base APK.

Does not patch, install, sign, execute, or upload an APK. Reports contain only
package/resource/method names and redacted instructions, never user data, URLs,
credentials, or APK bytes. A matching name alone does not prove functionality.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from inspect_apk import DEX_NAME, EXPECTED_PACKAGE, safe_sample

SIZE = 46035628
SHA256 = '8cf8c697d2ce04350d2a7fc7d301751e8bb30cf98f298d288ba8b9bfe3f7b1b2'
VERSION = 'v7.5.00307'
CODE = '50350'
KEYWORDS = re.compile(r'(?i)(premium|purchased|purchase|subscript|billing|licen[cs]e|entitle|ad.?free|unlocked|upgrade|sign.?in|sign.?out|microg|play.?services|is.?pro|pro.?user)')
RESOURCE_WORDS = re.compile(r'(?i)(premium|purchase|subscript|billing|licen[cs]e|account|sign.?in|sign.?out|upgrade|simple_mode_settings|settings|translate_failed)')
STRING_ANCHOR = re.compile(r'(?i)^(?:is[_-]?)?(?:premium|pro|purchased|subscribed|subscription|purchase|billing|license|licence|entitlement|ad[_-]?free|unlocked|upgrade|sign[_-]?in|google[_-]?sign[_-]?in|google[_-]?account|microg)(?:[_-](?:user|status|state|enabled|active|key|version))?$|^com\.google\.android\.gms$')
CLASS_WORDS = re.compile(r'(?i)(premium|purchas|subscript|billing|licen[cs]e|entitle|sign.?in|account)')
OLD_OWNERS = frozenset({'Lbe4;', 'Lkb9;', 'Lxm;', 'Ldv0;', 'Ld29;', 'Lqy8;', 'Lmr0;',
                        'Lbin/edisaputra/protector/LicenseActivity;',
                        'Lcom/spaceship/screen/translate/SSApplication;',
                        'Lcom/spaceship/screen/translate/ui/MainActivity;'})
GMS_CALLS = ('Lcom/google/android/gms/auth/', 'Lcom/google/android/gms/common/GoogleApiAvailability',
             'Lcom/google/android/gms/common/GoogleSignatureVerifier;', 'Lcom/google/firebase/auth/')


def method_id(cls, method):
    return cls.get_name() + '->' + method.get_name() + ''.join(method.get_descriptor().split())


def sanitize(inst):
    op, raw = inst.get_name(), inst.get_output()
    if op.startswith('const-string'):
        register = raw.split(',', 1)[0].strip()
        match = re.search(r'"(.*?)"', raw)
        value = match.group(1) if match else ''
        allowed = value if STRING_ANCHOR.fullmatch(value) and safe_sample(value) else '<redacted>'
        return {'op': op, 'value': register + ',' + allowed}
    if '"' in raw or "'" in raw or 'http://' in raw.lower() or 'https://' in raw.lower() or len(raw) > 500:
        return {'op': op, 'value': '<redacted>'}
    return {'op': op, 'value': re.sub(r'\s+', '', raw)}


def candidate_owner(owner):
    return owner.startswith('Lcom/spaceship/') or bool(re.fullmatch(r'L[A-Za-z0-9_$]+;', owner))


def verify(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1048576), b''):
            h.update(chunk)
    if path.stat().st_size != SIZE or h.hexdigest() != SHA256 or not zipfile.is_zipfile(path):
        raise ValueError('Release base APK differs from the pinned asset')


def trace(path):
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    from lxml import etree
    logger.remove()
    verify(path)
    apk = APK(str(path))
    if (not apk.is_valid_APK() or apk.get_package() != EXPECTED_PACKAGE or
            apk.get_androidversion_name() != VERSION or str(apk.get_androidversion_code()) != CODE):
        raise ValueError('Unexpected target identity')

    resources = apk.get_android_resources()
    resource_entries, resource_anchors = [], {}
    for package in resources.get_packages_names():
        root = etree.fromstring(resources.get_string_resources(package))
        for item in root.iter('string'):
            name = item.get('name', '')
            text = ''.join(item.itertext()).strip()
            if not RESOURCE_WORDS.search(name) or not safe_sample(name):
                continue
            entry = {'name': name}
            identifier = resources.get_res_id_by_key(package, 'string', name)
            if isinstance(identifier, int):
                entry['id'] = f'0x{identifier:08x}'
                resource_anchors[identifier] = name
            if safe_sample(text): entry['text'] = text
            resource_entries.append(entry)

    named, keyword_strings, old_classes = [], Counter(), {}
    keyword_refs, resource_refs, gms_refs = defaultdict(list), defaultdict(list), defaultdict(list)
    method_bodies = {}
    scanned = 0
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if not DEX_NAME.fullmatch(info.filename): continue
            dex = DEX(archive.read(info))
            for value in dex.get_strings():
                if isinstance(value, str) and KEYWORDS.search(value) and safe_sample(value):
                    keyword_strings[value] += 1
            for cls in dex.get_classes():
                owner = cls.get_name()
                methods = list(cls.get_methods())
                if owner in OLD_OWNERS:
                    old_classes[owner] = {
                        'dex': info.filename,
                        'fields': [{'name': f.get_name(), 'type': ''.join(f.get_descriptor().split()),
                                    'access': f.get_access_flags_string()} for f in cls.get_fields()],
                        'methods': [method_id(cls, m) for m in methods],
                    }
                if owner.startswith('Lcom/spaceship/') and CLASS_WORDS.search(owner):
                    named.append({'class': owner, 'dex': info.filename,
                                  'fields': [{'name': f.get_name(), 'type': ''.join(f.get_descriptor().split())}
                                             for f in cls.get_fields()],
                                  'methods': [method_id(cls, m) for m in methods]})
                if not candidate_owner(owner): continue
                for method in methods:
                    code = method.get_code()
                    if code is None: continue
                    scanned += 1
                    ident = method_id(cls, method)
                    instructions = list(method.get_instructions())
                    keep_body = owner in OLD_OWNERS and (owner != 'Lcom/spaceship/screen/translate/ui/MainActivity;' or method.get_name() in ('onCreate', 'attachBaseContext'))
                    for index, inst in enumerate(instructions):
                        op, raw = inst.get_name(), inst.get_output()
                        anchors = []
                        if op.startswith('const-string'):
                            match = re.search(r'"(.*?)"', raw)
                            value = match.group(1) if match else ''
                            if STRING_ANCHOR.fullmatch(value) and safe_sample(value):
                                anchors.append(('string', value))
                        elif op.startswith('const'):
                            for literal in inst.get_literals():
                                if literal in resource_anchors:
                                    anchors.append(('resource', resource_anchors[literal]))
                        if op.startswith('invoke-'):
                            for gms in GMS_CALLS:
                                if gms in raw:
                                    target = ''.join(raw.split()).rsplit(',', 1)[-1]
                                    if len(gms_refs[gms]) < 50:
                                        gms_refs[gms].append({'method': ident, 'dex': info.filename, 'target': target})
                        for kind, anchor in anchors:
                            bucket = keyword_refs if kind == 'string' else resource_refs
                            if len(bucket[anchor]) < 14:
                                bucket[anchor].append({'method': ident, 'dex': info.filename, 'index': index,
                                    'instructions': [sanitize(x) for x in instructions[max(0,index-9):min(len(instructions),index+13)]]})
                            if anchor in {'simple_mode_settings', 'simple_mode_settings_desc', 'translate_failed',
                                          'is_premium', 'isPremium', 'premium', 'is_pro', 'isPro', 'purchased'}:
                                keep_body = True
                    if keep_body and len(instructions) <= 400:
                        method_bodies[ident] = {'dex': info.filename, 'registers': code.get_registers_size(),
                            'incoming_registers': code.get_ins_size(), 'access': method.get_access_flags_string(),
                            'instructions': [sanitize(x) for x in instructions]}
            del dex
            gc.collect()
    return {'scope': 'Read-only static base APK scan; no patch, signing, installation, execution or credentials',
            'sha256': SHA256, 'package': EXPECTED_PACKAGE, 'version': VERSION, 'version_code': CODE,
            'resources': resource_entries, 'named_classes': named,
            'keyword_strings': dict(sorted(keyword_strings.items())), 'old_hook_classes': old_classes,
            'keyword_references': dict(keyword_refs), 'resource_references': dict(resource_refs),
            'google_services_references': dict(gms_refs), 'method_bodies': method_bodies,
            'scanned_methods': scanned}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(trace(args.apk), indent=2, ensure_ascii=False) + '\n')
    print('Sanitized read-only feature scan written')


if __name__ == '__main__': main()
