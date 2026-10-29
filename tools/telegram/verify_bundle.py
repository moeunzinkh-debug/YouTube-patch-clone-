#!/usr/bin/env python3
"""Verify the isolated Telegram-only MPP and actual Morphe Desktop listing."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
METADATA = ROOT / 'bundles/telegram/upstream-patches.json'
METADATA_SHA256 = '606d40dc43bda9cb6bceb96bc521208c7f1eea7d814b820474e8a926d5347bdd'
COMMIT = '92c0fca0ae103a419c7fc61f9c5b8b38b7d6b82a'
VERSION = '1.23.1-tg.1'
TARGETS = {
    'org.telegram.messenger': ('12.10.1', 70382),
    'org.telegram.messenger.web': ('12.10.1', 70389),
    'org.telegram.plus': ('12.10.1.1', 22510),
}
NAMES = {
    'Anti-delete messages', 'Anti-disappearing media', 'Anti-screenshot notification',
    'Bypass channel restrictions', 'Bypass content restrictions', 'Bypass integrity check',
    'Disable analytics', 'Disable auto-update', 'Disable channel switching', 'Download speed boost',
    'Hide typing indicator', 'Remove ads', 'Unlock Premium', 'Use normal paste', 'Voice to music',
}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def metadata() -> dict:
    data = METADATA.read_bytes()
    check(hashlib.sha256(data).hexdigest() == METADATA_SHA256, 'Pinned upstream metadata changed')
    source = json.loads(data)
    check(source['upstream_tag'] == 'v1.23.1' and source['upstream_commit'] == COMMIT,
          'Incorrect upstream attribution')
    entries = source['patches']
    check(len(entries) == len(NAMES), 'Expected exactly 15 unique Telegram selectors')
    check({p['name'] for p in entries} == NAMES, 'Telegram selector set changed')
    check(len({p['name'] for p in entries}) == len(entries), 'Duplicate Telegram selectors')
    for patch in entries:
        check(patch.get('default') is True, 'Unexpected upstream default: ' + patch['name'])
        expected = {'org.telegram.plus'} if patch['name'] == 'Disable analytics' else set(TARGETS)
        packages = patch['compatiblePackages']
        check({p['packageName'] for p in packages} == expected, 'Unexpected compatible package: ' + patch['name'])
        for package in packages:
            version, code = TARGETS[package['packageName']]
            targets = package['targets']
            check(len(targets) == 1 and targets[0]['version'] == version,
                  'Unexpected target version for ' + patch['name'])
            check(set(targets[0]['versionCodes'].values()) == {code},
                  'Unexpected version code for ' + patch['name'])
        check(patch.get('options') == [], 'Unexpected named-selector options')
    return source


def verify_archive(path: Path) -> dict:
    check(path.is_file() and zipfile.is_zipfile(path), 'Missing or invalid MPP')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as archive:
        check(archive.testzip() is None, 'MPP ZIP integrity error')
        names = archive.namelist()
        check(len(names) == len(set(names)), 'Duplicate archive entries')
        for required in ('META-INF/MANIFEST.MF', 'classes.dex', 'extensions/extension.mpe'):
            check(required in names and archive.getinfo(required).file_size > 0, 'Missing MPP component: ' + required)
        manifest = archive.read('META-INF/MANIFEST.MF').decode('utf-8').replace('\r\n ', '').replace('\r', '')
        check('Version: ' + VERSION + '\n' in manifest, 'Unexpected MPP version')
        check('Patcher-Version: 1.8.0\n' in manifest, 'Unexpected Morphe Patcher API version')
        check('Telegram Patch Clone' in manifest, 'Fork must have distinct branding')
        check('rushiranpise' in manifest, 'Missing upstream attribution')
        project_classes = [n for n in names if n.startswith('app/template/patches/') and n.endswith('.class')]
        check(project_classes and all(n.startswith(('app/template/patches/telegram/',
                                                      'app/template/patches/shared/')) for n in project_classes),
              'Non-Telegram patch classes found')
        check(any('TelegramRemoveAdsPatchKt' in n for n in project_classes), 'Missing Telegram patch classes')
        extension = archive.read('extensions/extension.mpe')
        check(extension.startswith(b'dex\n') and b'SignatureHookApp' in extension and b'InstallSourceHelper' in extension,
              'Missing necessary Telegram signature/install-source helpers')
    return {'sha256': digest, 'bytes': path.stat().st_size}


def verify_listing(text: str, source: dict) -> None:
    matches = list(re.finditer(r'^Name: (.+)$', text, flags=re.MULTILINE))
    check(len(matches) == 15, f'Morphe listed {len(matches)} named patches instead of 15')
    expected = {p['name']: p for p in source['patches']}
    seen = set()
    for i, match in enumerate(matches):
        name = match.group(1).strip()
        check(name in expected and name not in seen, 'Unexpected or duplicate selectable patch: ' + name)
        seen.add(name)
        block = text[match.start(): matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        enabled = re.findall(r'^Enabled: (true|false)$', block, flags=re.MULTILINE | re.IGNORECASE)
        check(enabled == ['true'], 'Unexpected default in Morphe listing: ' + name)
        packages = re.findall(r'^\s*Package name: (\S+)', block, flags=re.MULTILINE)
        expected_packages = {c['packageName'] for c in expected[name]['compatiblePackages']}
        check(len(packages) == len(expected_packages) and set(packages) == expected_packages,
              'Unexpected Morphe package listing: ' + name)
        for package in expected_packages:
            version, code = TARGETS[package]
            match_package = re.search(r'^\s*Package name: ' + re.escape(package) + r'\s*$', block, re.MULTILINE)
            rest = block[match_package.end():]
            next_package = re.search(r'^\s*Package name: ', rest, re.MULTILINE)
            package_block = rest[:next_package.start()] if next_package else rest
            check(re.search(r'^\s*' + re.escape(version) + r'\s*$', package_block, re.MULTILINE) is not None,
                  'Missing Morphe target version for ' + name + ': ' + package)
            check(str(code) in package_block, 'Missing Morphe version code for ' + name + ': ' + package)
    check(seen == NAMES, 'Morphe selector set differs from upstream Telegram')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mpp', type=Path)
    parser.add_argument('--listing', type=Path)
    args = parser.parse_args()
    source = metadata()
    if args.mpp:
        result = verify_archive(args.mpp)
        checksum = args.mpp.with_name(args.mpp.name + '.sha256')
        check(checksum.read_text().split()[0] == result['sha256'], 'MPP checksum mismatch')
        print('Verified Telegram-only bundle:', json.dumps(result))
    if args.listing:
        verify_listing(args.listing.read_text(), source)
        print('Morphe lists exactly 15 Telegram-only selectors with original defaults and targets')
    if not args.mpp and not args.listing:
        print('Verified 15 pinned Telegram metadata records')


if __name__ == '__main__':
    main()
