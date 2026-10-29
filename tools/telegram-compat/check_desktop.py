#!/usr/bin/env python3
"""Patch a verified fixture with the exact Patcher generation in the user's log.

No account data is used. The Web sample was verified separately by SHA-256;
the standard Telegram sample is accepted only after an Android signature and
package/version check by inspect_artifact.py.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('/tmp/telegram-compat')
DESKTOP = OUT / 'morphe-desktop-1.20.0-dev.1-all.jar'  # Patcher 2.1.0-dev.1
MPP = ROOT / 'bundles/telegram-email-experimental/bundle.mpp'
EXPERIMENT = 'Try another login method (experimental)'
SELECTORS = ('Disable auto-update', EXPERIMENT)


def attempt(apk: Path, package: str, selector: str) -> bool:
    slug = 'update' if selector == SELECTORS[0] else 'email'
    output = OUT / f'{package}-{slug}.apk'
    report = OUT / f'{package}-{slug}.json'
    cmd = ['java', '-Xmx4g', '-jar', str(DESKTOP), 'patch', str(apk), '-p', str(MPP),
           '--exclusive', '-e', selector, '--unsigned', '-o', str(output), '-r', str(report)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=480)
    if proc.returncode == 0 and output.is_file() and report.is_file():
        data = json.loads(report.read_text())
        if (data.get('success') is True and not data.get('failedPatches') and
                set(data.get('appliedPatches', [])) == {selector} and
                data.get('packageName') == package and data.get('packageVersion') == '12.10.1'):
            print(f'::notice::{package} 12.10.1: {selector} alone PASSED with Morphe Patcher 2.1.0-dev.1', flush=True)
            return True
    lines = [line.strip() for line in proc.stdout.splitlines()
             if any(word in line.lower() for word in ('failed', 'error', 'exception', 'fingerprint'))]
    short = ' | '.join(lines[-5:])[:1600] or f'exit={proc.returncode}; report missing or incomplete'
    print(f'::warning::{package} 12.10.1: {selector} alone DID NOT PASS: {short}', flush=True)
    return False


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit('usage: check_desktop.py input.apk package')
    apk, package = Path(sys.argv[1]), sys.argv[2]
    if package not in ('org.telegram.messenger', 'org.telegram.messenger.web'):
        raise ValueError('Unrecognized fixture package')
    results = {selector: attempt(apk, package, selector) for selector in SELECTORS}
    (OUT / f'{package}-results.json').write_text(json.dumps(results, indent=2) + '\n')
    # Do not hide a regression in the already-verified Web fixture. The standard
    # case is investigative: a selector failure is a finding, not a passed patch.
    if package.endswith('.web') and not all(results.values()):
        raise SystemExit('Web regression in the selected patcher generation')


if __name__ == '__main__':
    main()
