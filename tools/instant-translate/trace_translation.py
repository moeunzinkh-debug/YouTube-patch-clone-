#!/usr/bin/env python3
"""Locate translation failure anchors and call sites in the pinned APK's DEX.

The report contains class/method identifiers, sanitized instruction windows and
public hostname-only clues. It never emits arbitrary string literals, URLs,
queries, credentials, or APK bytes. Static anchors alone do not prove root cause.
"""
from __future__ import annotations

import argparse
import gc
import ipaddress
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from inspect_apk import DEX_NAME, EXPECTED_PACKAGE, verify_asset

ANCHORS = frozenset({
    'Both offline and online translation failed.',
    'Online translation failed, no offline result available.',
    'Error translating',
    'translate_batch_client_error',
    'translate_batch_fail',
    'translate_by_end_point_fail',
    'translate_fail_use_server',
    'Translation failed',
})
RESOURCE_NAMES = (
    'translate_failed', 'offline_translate', 'offline_then_online_translate',
    'double_translate_describe', 'offline_translate_describe',
)
TRANSLATE = re.compile(r'translat|deepl|bing|microsofttranslator', re.I)
SAFE_HOST = re.compile(r'(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}\Z')
URL = re.compile(r'https?://[^\s<>"\']+', re.I)


def output_host(value: str) -> str | None:
    """Extract a public DNS hostname only, never credentials, URLs, paths or queries."""
    if not TRANSLATE.search(value):
        return None
    match = URL.search(value)
    if not match:
        return None
    try:
        host = (urlsplit(match.group()).hostname or '').lower()
    except ValueError:
        return None
    if not SAFE_HOST.fullmatch(host):
        return None
    try:
        ipaddress.ip_address(host)
        return None
    except ValueError:
        return host


def sanitize_instruction(inst) -> dict[str, str]:
    op = inst.get_name()
    raw = inst.get_output()
    if op.startswith('const-string'):
        anchor = next((value for value in ANCHORS if value in raw), None)
        return {'op': op, 'value': anchor or '<redacted>'}
    if 'http://' in raw.lower() or 'https://' in raw.lower() or '"' in raw or "'" in raw:
        return {'op': op, 'value': '<redacted>'}
    if len(raw) > 500 or not raw.isprintable():
        return {'op': op, 'value': '<redacted>'}
    return {'op': op, 'value': re.sub(r'\s+', '', raw)}


def method_id(cls, method) -> str:
    return cls.get_name() + '->' + method.get_name() + ''.join(method.get_descriptor().split())


def collect_resource_ids(apk) -> dict[str, int]:
    resources = apk.get_android_resources()
    if resources is None:
        return {}
    result = {}
    for name in RESOURCE_NAMES:
        value = resources.get_res_id_by_key(EXPECTED_PACKAGE, 'string', name)
        if isinstance(value, int):
            result[name] = value
    return result


def trace(path: Path) -> dict:
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    logger.remove()
    verify_asset(path)
    apk = APK(str(path))
    if not apk.is_valid_APK() or apk.get_package() != EXPECTED_PACKAGE:
        raise ValueError('Unexpected APK identity')
    resource_ids = collect_resource_ids(apk)
    if 'translate_failed' not in resource_ids:
        raise ValueError('Expected translation-failure resource was not found')
    # Other IDs are useful UI context but too broad to trace as failure paths.
    interesting_ids = {resource_ids['translate_failed']}
    hits: list[dict] = []
    public_hosts = Counter()
    strings_found = Counter()
    interesting_classes = set()
    app_namespace = 'Lcom/spaceship/screen/translate/'
    methods_seen = 0
    with zipfile.ZipFile(path) as archive:
        dex_names = [info.filename for info in archive.infolist() if DEX_NAME.fullmatch(info.filename)]
        for dex_name in dex_names:
            dex = DEX(archive.read(dex_name))
            for value in dex.get_strings():
                if not isinstance(value, str):
                    continue
                if value in ANCHORS:
                    strings_found[value] += 1
                host = output_host(value)
                if host:
                    public_hosts[host] += 1
            for cls in dex.get_classes():
                name = cls.get_name()
                # Exclude the common application package, which itself ends in "translate".
                if name.startswith(app_namespace) and TRANSLATE.search(name.removeprefix(app_namespace)):
                    interesting_classes.add(name)
                for method in cls.get_methods():
                    code = method.get_code()
                    if code is None:
                        continue
                    methods_seen += 1
                    instructions = list(method.get_instructions())
                    matched = []
                    for i, ins in enumerate(instructions):
                        op = ins.get_name()
                        if op.startswith('const-string'):
                            out = ins.get_output()
                            for anchor in ANCHORS:
                                if anchor in out:
                                    matched.append((i, anchor))
                        elif op.startswith('const'):
                            for value in ins.get_literals():
                                if isinstance(value, int) and value in interesting_ids:
                                    matched.append((i, next(key for key, item in resource_ids.items() if item == value)))
                    if matched:
                        windows = []
                        for index, anchor in matched[:5]:
                            start, end = max(0, index - 5), min(len(instructions), index + 9)
                            windows.append({'anchor': anchor, 'instruction_index': index,
                                            'instructions': [sanitize_instruction(item) for item in instructions[start:end]]})
                        hits.append({'dex': dex_name, 'method': method_id(cls, method), 'windows': windows})
            del dex
            gc.collect()
        wanted = {item['method'] for item in hits}
        callers = defaultdict(set)
        if wanted:
            # Only exact method reference identifiers are recorded, never literal strings.
            for dex_name in dex_names:
                dex = DEX(archive.read(dex_name))
                for cls in dex.get_classes():
                    for method in cls.get_methods():
                        if method.get_code() is None:
                            continue
                        for ins in method.get_instructions():
                            if not ins.get_name().startswith('invoke-'):
                                continue
                            out = ''.join(ins.get_output().split())
                            # Method references contain no comma; registers appear before it.
                            target = out.rsplit(',', 1)[-1]
                            if target in wanted and len(callers[target]) < 30:
                                callers[target].add(method_id(cls, method))
                del dex
                gc.collect()
    return {
        'scope': 'Static DEX/resource anchor search only. No app execution, provider requests or patching.',
        'asset_sha256': 'f341a1b174bda7b5d1c95cb2fc84da238228a116844069ee962220acaf1e4e4c',
        'package': EXPECTED_PACKAGE, 'version': apk.get_androidversion_name(), 'code': apk.get_androidversion_code(),
        'resource_ids': {key: f'0x{value:08x}' for key, value in resource_ids.items()},
        'public_hostnames_from_translation_related_urls': dict(sorted(public_hosts.items())),
        'anchor_string_occurrences': dict(sorted(strings_found.items())),
        'translation_related_app_classes': sorted(interesting_classes)[:160],
        'methods_scanned': methods_seen, 'matches': hits[:100],
        'direct_callers': {key: sorted(values) for key, values in sorted(callers.items())},
        'note': 'Hostname/string presence does not prove the user\'s active engine, a request or root cause.',
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    report = trace(args.apk)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'resource_ids': report['resource_ids'], 'hostnames': report['public_hostnames_from_translation_related_urls'],
                      'methods_scanned': report['methods_scanned'], 'match_count': len(report['matches'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
