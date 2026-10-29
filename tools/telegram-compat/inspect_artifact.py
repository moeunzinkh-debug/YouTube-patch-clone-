#!/usr/bin/env python3
"""Find a genuine 12.10.1 standard Telegram APK in a public test artifact.

Never execute or distribute a foreign APK. Both identity and original signer
are mandatory before the candidate can be used for static patch tests.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

CERT = '49c1522548ebacd46ce322b6fd47f6092bb745d0f88082145caf35e14dcc38e1'
MAX_BYTES = 250 * 1024 * 1024


def build_tool(name: str) -> Path:
    home = Path(os.environ['ANDROID_HOME']) / 'build-tools'
    versions = sorted((p for p in home.iterdir() if (p / name).is_file()),
                      key=lambda p: tuple(int(x) for x in re.findall(r'\d+', p.name)))
    if not versions:
        raise RuntimeError(f'{name} was not found')
    return versions[-1] / name


def main() -> None:
    root, target = map(Path, sys.argv[1:])
    aapt, signer = build_tool('aapt'), build_tool('apksigner')
    files = [p for p in root.rglob('*') if p.is_file() and p.stat().st_size <= MAX_BYTES]
    if not files:
        print('::warning::The public artifact did not contain inspectable files', flush=True)
        return
    print('::notice::Public artifact files: ' + ', '.join(f'{p.name} ({p.stat().st_size} bytes)' for p in files)[:1000], flush=True)
    candidates = [p for p in files if zipfile.is_zipfile(p)]
    # An APK bundle may store the base APK in a container. Copy only bounded
    # members into a disposable directory; never unpack paths from the archive.
    nested = target.parent / 'nested-candidates'
    nested.mkdir(exist_ok=True)
    for archive_path in list(candidates):
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                if info.filename.endswith('.apk') and 1_000_000 < info.file_size <= MAX_BYTES:
                    dest = nested / f'{len(candidates)}.apk'
                    with archive.open(info) as source, dest.open('wb') as out:
                        shutil.copyfileobj(source, out, 1024 * 1024)
                    candidates.append(dest)
    seen = []
    for candidate in candidates:
        result = subprocess.run([str(aapt), 'dump', 'badging', str(candidate)], text=True, capture_output=True)
        package_line = next((line for line in result.stdout.splitlines() if line.startswith('package:')), '')
        if not package_line:
            continue
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        seen.append(f'{package_line}; sha256={digest}')
        if not ("name='org.telegram.messenger'" in package_line and "versionCode='70382'" in package_line
                and "versionName='12.10.1'" in package_line):
            continue
        verified = subprocess.run([str(signer), 'verify', '--verbose', '--print-certs', str(candidate)],
                                  text=True, capture_output=True)
        if verified.returncode != 0 or 'Number of signers: 1' not in verified.stdout or CERT not in verified.stdout.lower():
            seen.append('candidate rejected: Telegram original signer was not verified')
            continue
        shutil.copyfile(candidate, target)
        print(f'::notice::Verified standard Telegram 12.10.1 (70382), original signer, sha256={digest}', flush=True)
        return
    if seen:
        print('::notice::Artifact candidates (not accepted as the exact requested APK): ' + ' | '.join(seen)[:1700], flush=True)
    print('::warning::No original-signed standard Telegram 12.10.1 APK was available for this investigation.', flush=True)


if __name__ == '__main__':
    main()
