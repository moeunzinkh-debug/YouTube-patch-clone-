"""Resolve reuploaded APKs by expected digest, not release tag or filename."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

EXPECTED = {
    'gemini': 'bfa9b10060a1c0e8a1c3f2b01cd513f74a53b364ab9bdb1bca02ae103de3f7e5',
    'google': 'f9e5d898a8bae360e6d8654f1871b920e1a2774701fe716f4e64bb0c803b7bd9',
}


def resolve(releases):
    return {key: next((a for r in releases for a in r['assets']
                       if a.get('digest') == 'sha256:' + digest), None)
            for key, digest in EXPECTED.items()}


def main():
    repo = os.environ['GITHUB_REPOSITORY']
    raw = subprocess.check_output(['gh', 'api', '--paginate', '--slurp', f'repos/{repo}/releases?per_page=100'])
    releases = [release for page in json.loads(raw) for release in page]
    selected = resolve(releases)
    missing = [key for key, asset in selected.items() if asset is None]
    if missing:
        print('::warning::Exact uploaded APKs not found by digest: ' + ', '.join(missing))
    else:
        for key, asset in selected.items():
            path = Path(os.environ['RUNNER_TEMP']) / key / 'base.apk'
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('wb') as out:
                subprocess.run(['gh', 'api', f'repos/{repo}/releases/assets/{asset["id"]}',
                                '-H', 'Accept: application/octet-stream'], stdout=out, check=True)
            if hashlib.sha256(path.read_bytes()).hexdigest() != EXPECTED[key]:
                raise ValueError(f'{key}: downloaded APK SHA-256 mismatch')
            print(f'{key}: verified release asset {asset["id"]} ({asset["name"]})')
    with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
        out.write('available=' + ('false' if missing else 'true') + '\n')
    if missing and os.environ.get('REQUIRE_APK_TESTS') == 'true':
        sys.exit('Required exact APK test inputs unavailable')


if __name__ == '__main__':
    main()
