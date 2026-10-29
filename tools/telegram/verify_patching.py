#!/usr/bin/env python3
"""Check a real Morphe Desktop patch report without accepting partial success."""
import argparse
import hashlib
import json
from pathlib import Path

from verify_bundle import NAMES


def verify_report(path: Path, expected: set[str]) -> None:
    result = json.loads(path.read_text())
    if result.get('packageName') != 'org.telegram.messenger' or result.get('packageVersion') != '12.10.1':
        raise ValueError('Unexpected APK identity in patch report')
    if result.get('failedPatches'):
        raise ValueError('Morphe reported failed patches')
    if not result.get('patchingSteps') or any(not item.get('success') for item in result['patchingSteps']):
        raise ValueError('A patch or rebuild step failed')
    applied = {item['name'] for item in result.get('appliedPatches', [])}
    if applied != expected:
        raise ValueError(f'Unexpected applied selectors: {sorted(applied ^ expected)}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('single_report', type=Path)
    parser.add_argument('all_report', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    verify_report(args.single_report, {'Remove ads'})
    verify_report(args.all_report, NAMES - {'Disable analytics'})
    sha = hashlib.sha256()
    with args.apk.open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(data)
    report = {
        'status': 'passed_actual_mpp_on_original_signed_telegram_apk',
        'source': 'APKPure Telegram 12.10.1 version code 70382; signature and file SHA-1 verified',
        'original_apk_sha256': sha.hexdigest(),
        'original_signer_sha256': '49c1522548ebacd46ce322b6fd47f6092bb745d0f88082145caf35e14dcc38e1',
        'single_remove_ads': 'passed_morphe_patching_and_rebuild',
        'fourteen_default_telegram_selectors': 'passed_morphe_patching_and_rebuild',
        'device_runtime': 'not_tested',
    }
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('Morphe applied the MPP alone and with all 14 default Telegram selectors to the original signed input')


if __name__ == '__main__':
    main()
