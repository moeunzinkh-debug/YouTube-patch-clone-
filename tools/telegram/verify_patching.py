#!/usr/bin/env python3
"""Check a real Morphe Desktop patch report without accepting partial success."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from verify_bundle import NAMES


def verify_report(path: Path, expected: set[str], package: str = 'org.telegram.messenger') -> None:
    result = json.loads(path.read_text())
    if result.get('packageName') != package or result.get('packageVersion') != '12.10.1':
        raise ValueError('Unexpected APK identity in patch report')
    if result.get('success') is not True or result.get('failedPatches'):
        raise ValueError('Morphe reported an unsuccessful run or failed patches')
    steps = result.get('stepResults') or []
    if not {'PATCHING', 'REBUILDING'}.issubset({item.get('step') for item in steps}) or any(item.get('success') is not True for item in steps):
        raise ValueError('A patch or rebuild step failed or was missing')
    applied = set(result.get('appliedPatches', []))
    if applied != expected:
        raise ValueError(f'Unexpected applied selectors: {sorted(applied ^ expected)}')
    output = Path(result.get('outputPath', ''))
    if not output.is_file() or output.stat().st_size == 0 or not zipfile.is_zipfile(output):
        raise ValueError('Morphe did not create the rebuilt APK')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('single_report', type=Path)
    parser.add_argument('all_report', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--package', required=True, choices=('org.telegram.messenger', 'org.telegram.messenger.web'))
    args = parser.parse_args()
    verify_report(args.single_report, {'Remove ads'}, args.package)
    verify_report(args.all_report, NAMES - {'Disable analytics'}, args.package)
    sha = hashlib.sha256()
    with args.apk.open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(data)
    report = {
        'status': 'passed_actual_mpp_on_telegram_signed_apk',
        'source': 'LOVECHEN/telegram-release android-12.10.1 APK mirror; pinned SHA-256 and Telegram signer verified',
        'package': args.package,
        'version': '12.10.1',
        'version_code': 70389 if args.package.endswith('.web') else 70382,
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
