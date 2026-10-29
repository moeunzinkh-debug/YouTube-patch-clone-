#!/usr/bin/env python3
"""Verify the isolated experimental Telegram MPP and its actual Desktop selector listing."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/telegram'))
import verify_bundle as stable  # noqa: E402

VERSION = '1.23.1-tg.email-exp.1'
SELECTOR = 'Try another login method (experimental)'
PACKAGES = {'org.telegram.messenger', 'org.telegram.messenger.web'}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_archive(path: Path) -> dict:
    old = stable.VERSION
    stable.VERSION = VERSION
    try:
        result = stable.verify_archive(path)
    finally:
        stable.VERSION = old
    with zipfile.ZipFile(path) as archive:
        check(any('TelegramEmailAlternativePatchKt' in name for name in archive.namelist()),
              'Missing custom bytecode patch')
        extension = archive.read('extensions/extension.mpe')
        check(b'EmailAlternative' in extension and b'phone_code_hash' in extension,
              'Missing experimental runtime helper')
    return result


def verify_listing(text: str) -> None:
    matches = list(re.finditer(r'^Name: (.+)$', text, flags=re.MULTILINE))
    check(len(matches) == 16, f'Expected 15 upstream selectors and one experiment; found {len(matches)}')
    indices = [i for i, m in enumerate(matches) if m.group(1).strip() == SELECTOR]
    check(len(indices) == 1, 'Missing or duplicated experiment selector')
    i = indices[0]
    start = matches[i].start()
    end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
    block = text[start:end]
    enabled = re.findall(r'^Enabled: (true|false)$', block, flags=re.MULTILINE | re.IGNORECASE)
    check(enabled == ['false'], 'Experiment must be opt-in by default')
    packages = re.findall(r'^\s*Package name: (\S+)', block, flags=re.MULTILINE)
    check(len(packages) == 2 and set(packages) == PACKAGES, 'Experiment has unexpected package targets')
    for package in PACKAGES:
        version, code = stable.TARGETS[package]
        match = re.search(r'^\s*Package name: ' + re.escape(package) + r'\s*$', block, re.MULTILINE)
        rest = block[match.end():]
        next_package = re.search(r'^\s*Package name: ', rest, re.MULTILINE)
        package_block = rest[:next_package.start()] if next_package else rest
        check(re.search(r'^\s*' + re.escape(version) + r'\s*$', package_block, re.MULTILINE) is not None,
              'Missing exact experiment target version: ' + package)
        check(str(code) in package_block, 'Missing exact experiment target version code: ' + package)
    stable.verify_listing(text[:start] + text[end:], stable.metadata())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mpp', type=Path)
    parser.add_argument('--listing', type=Path)
    args = parser.parse_args()
    if args.mpp:
        result = verify_archive(args.mpp)
        checksum = args.mpp.with_name(args.mpp.name + '.sha256')
        check(checksum.read_text().split()[0] == result['sha256'], 'MPP checksum mismatch')
        print('Verified separate experiment archive:', json.dumps(result))
    if args.listing:
        verify_listing(args.listing.read_text(encoding='utf-8'))
        print('Verified 15 original selectors plus one default-off experiment')
    check(args.mpp is not None or args.listing is not None, 'Provide an MPP or a listing')


if __name__ == '__main__':
    main()
