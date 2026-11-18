#!/usr/bin/env python3
"""Bounded static inspection for GenV ad SDKs and non-entitlement feature gates.

The SHA-pinned APK is never installed or modified. The report contains package,
class and method identifiers only; arbitrary strings, URLs, tokens and user data
are never emitted.
"""
from __future__ import annotations
import argparse
import gc
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

ASSET = 'GenV_3.7.2.apk'
SIZE = 23281657
SHA256 = 'f50a9d162a5802ce30ba842c09d08c8c2b2c816dc439eb1b8c0346aa71501d2e'
PACKAGE = 'com.ainate.ai.video.generate'
DEX = re.compile(r'classes(?:[2-9]|[1-9][0-9]+)?\.dex\Z')
AD = re.compile(r'google[/.$]android[/.$]gms[/.$]ads|google_mobile_ads|mobileads|applovin|iron(?:source)?|unity3d[/.$]ads|facebook[/.$]ads|pangle|vungle|startapp|admob', re.I)
GATE = re.compile(r'remote.?config|feature.?flag|premium|subscription|entitlement|ispro|profeature|paywall', re.I)
AD_METHOD = re.compile(r'^(?:load|show|hide|dispose|destroy|pause|resume|initialize|set|create).*(?:ad|banner|interstitial|reward)|^(?:loadAd|showAd)$', re.I)
GATE_METHOD = re.compile(r'(?:is|has|can|enable|available|visible|supported).*(?:feature|premium|pro|subscription|entitlement)|(?:feature|premium|paywall).*(?:is|has|enabled|available)', re.I)
SAFE = re.compile(r'^[A-Za-z0-9_/$;<>.()\[\]-]{1,240}$')
ANDROID = '{http://schemas.android.com/apk/res/android}'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked(path: Path) -> None:
    if path.name != ASSET or path.stat().st_size != SIZE or digest(path) != SHA256:
        raise ValueError('APK does not match the reviewed GenV release asset')


def safe(value: str) -> bool:
    return bool(SAFE.fullmatch(value)) and not re.search(r'https?|token|secret|password|key=', value, re.I)


def inspect(path: Path) -> dict:
    from androguard.core.apk import APK
    from androguard.core.dex import DEX as DexFile
    from loguru import logger
    logger.remove()
    checked(path)
    apk = APK(str(path))
    if apk.get_package() != PACKAGE or apk.get_androidversion_name() != '3.7.2' or apk.get_androidversion_code() != '163':
        raise ValueError('Unexpected GenV identity')
    manifest = apk.get_android_manifest_xml()
    manifest_matches = []
    for node in manifest.iter():
        name = node.get(ANDROID + 'name', '')
        if name and (AD.search(name) or GATE.search(name)) and safe(name):
            manifest_matches.append({'element': node.tag.rsplit('}', 1)[-1], 'name': name})
    classes = {'ads': set(), 'gates': set()}
    methods = {'ads': set(), 'gates': set()}
    candidates = {}
    counts = Counter()
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if not DEX.fullmatch(info.filename):
                continue
            dex = DexFile(archive.read(info))
            for value in dex.get_strings():
                if not isinstance(value, str):
                    continue
                if AD.search(value): counts['ad_related_strings'] += 1
                if GATE.search(value): counts['gate_related_strings'] += 1
            for cls in dex.get_classes():
                owner = cls.get_name()
                ad_owner, gate_owner = bool(AD.search(owner)), bool(GATE.search(owner))
                if ad_owner and safe(owner): classes['ads'].add(owner)
                if gate_owner and safe(owner): classes['gates'].add(owner)
                for method in cls.get_methods():
                    name = method.get_name()
                    descriptor = re.sub(r'\s+', '', method.get_descriptor())
                    identifier = f'{owner}->{name}{descriptor}'
                    ad_match = ad_owner or bool(AD_METHOD.search(name))
                    gate_match = gate_owner or bool(GATE_METHOD.search(name))
                    if ad_match and safe(identifier): methods['ads'].add(identifier)
                    if gate_match and safe(identifier): methods['gates'].add(identifier)
                    if method.get_code() is None or not safe(identifier):
                        continue
                    if (ad_owner and AD_METHOD.search(name)) or (gate_owner and GATE_METHOD.search(name)):
                        refs, opcodes = [], []
                        for instruction in method.get_instructions():
                            opcodes.append(instruction.get_name())
                            if instruction.get_name().startswith('invoke-'):
                                operand = instruction.get_output().replace(' ', '')
                                if safe(operand): refs.append(operand)
                        candidates[identifier] = {
                            'dex': info.filename,
                            'access': method.get_access_flags_string(),
                            'registers': method.get_code().get_registers_size(),
                            'opcodes': opcodes[:120],
                            'invoke_references': refs[:60],
                        }
            del dex
            gc.collect()
    flutter_entries = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if ('flutter_assets' in name and re.search(r'AssetManifest|NOTICES|FontManifest', name)
                    and safe(name.replace('/', '.'))):
                flutter_entries.append(name)
    checked(path)
    return {
        'scope': 'SHA-pinned GenV base; static identifiers only; no install, execution, account, network service, or APK output.',
        'source': {'filename': ASSET, 'size': SIZE, 'sha256': SHA256},
        'package': PACKAGE, 'version': '3.7.2', 'version_code': '163',
        'split_required': any(item.get('name') == 'com.android.vending.splits.required' for item in apk.get_android_manifest_xml().iter('meta-data')),
        'permissions': sorted(p for p in apk.get_permissions() if re.search(r'AD_ID|BILLING', p)),
        'manifest_matches': sorted(manifest_matches, key=lambda item: (item['element'], item['name'])),
        'string_counts': dict(sorted(counts.items())),
        'matched_classes': {key: sorted(value)[:400] for key, value in classes.items()},
        'matched_class_counts': {key: len(value) for key, value in classes.items()},
        'matched_methods': {key: sorted(value)[:700] for key, value in methods.items()},
        'matched_method_counts': {key: len(value) for key, value in methods.items()},
        'review_candidates': dict(sorted(candidates.items())),
        'flutter_metadata_entries': sorted(flutter_entries),
        'caveat': 'The released base requires splits and contains no native libraries. Dart AOT feature logic may be in a missing ABI split; identifiers do not prove runtime reachability.',
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('apk', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    report = inspect(args.apk)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'classes': report['matched_class_counts'], 'methods': report['matched_method_counts'],
                      'manifest_matches': len(report['manifest_matches']), 'candidates': len(report['review_candidates'])}))


if __name__ == '__main__':
    main()
