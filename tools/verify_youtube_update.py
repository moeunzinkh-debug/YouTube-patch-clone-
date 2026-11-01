#!/usr/bin/env python3
"""Verify the YouTube selectors, recommended target and compiled MPP.

This intentionally checks metadata plus Morphe Desktop's own patch listing;
it does not claim that applying patches or running an APK succeeded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tools/tests/data/youtube-patch-names.json'
VERSION = '2.0.0-dev.1'
PACKAGE = 'com.google.android.youtube'
TARGETS = [
    ('21.43.523', 29, True), ('21.42.241', 29, True),
    ('21.30.216', 29, False), ('21.28.208', 29, False),
    ('21.23.492', 28, False), ('20.51.39', 28, False),
    ('20.26.46', 26, False),
]
NEW_PATCHES = {'Download post images', 'Niconico comments', 'Search comments', 'Translate posts'}


def check(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def expected_names() -> set[str]:
    names = json.loads(FIXTURE.read_text(encoding='utf-8'))
    check(len(names) == 115 and len(set(names)) == 115, 'Unexpected selector fixture')
    return set(names)


def verify_catalog(data: dict) -> None:
    check(data['version'] == VERSION, 'Unexpected generated patch-list version')
    patches = data['patches']
    names = [p['name'] for p in patches]
    check(len(names) == len(set(names)) and set(names) == expected_names(), 'Unexpected selector names')
    check(NEW_PATCHES.issubset(names), 'An upstream YouTube selector is missing')
    youtube = generic = 0
    for patch in patches:
        packages = patch.get('compatiblePackages') or []
        if not packages:
            generic += 1
            continue
        check(len(packages) == 1 and packages[0]['packageName'] == PACKAGE,
              f"Non-YouTube patch target: {patch['name']}")
        youtube += 1
        observed = [(target.get('version'), target.get('minSdk'), target.get('isExperimental', False))
                    for target in packages[0].get('targets', [])]
        check(observed == TARGETS, f"Unexpected target list: {patch['name']}")
    check((youtube, generic) == (110, 5), 'Unexpected YouTube/generic counts')
    # Manager's default offered list omits experimental targets and picks the first stable one.
    check(next(v for v, _, experimental in TARGETS if not experimental) == '21.30.216',
          'Wrong default recommendation')


def verify_archive(path: Path) -> dict:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    check(path.with_name(path.name + '.sha256').read_text().split()[0] == digest, 'MPP checksum mismatch')
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        check(len(names) == len(set(names)) and z.testzip() is None, 'Invalid MPP archive')
        manifest = z.read('META-INF/MANIFEST.MF').decode().replace('\r\n ', '').replace('\r', '')
        check(f'Version: {VERSION}\n' in manifest, 'Wrong MPP version')
        check('Patcher-Version: 2.0.0\n' in manifest, 'Wrong Patcher version')
        check('YouTube Patch Clone' in manifest, 'Fork branding missing')
        for path in ('video/audio/EqualizerPatchKt.class',
                     'interaction/postimages/PostImageDownloadPatchKt.class',
                     'interaction/posttranslate/PostTranslatePatchKt.class',
                     'interaction/searchcomments/SearchCommentsPatchKt.class',
                     'layout/niconicocomments/NiconicoCommentsPatchKt.class'):
            check('app/morphe/patches/youtube/' + path in names, 'Patch class missing: ' + path)
        check(not any(n.startswith(('app/morphe/patches/music/', 'app/morphe/patches/reddit/'))
                      for n in names), 'Music/Reddit patch class present')
        check('classes.dex' in names and z.read('classes.dex').startswith(b'dex\n'),
              'Android patch-code DEX missing; Manager cannot load a JVM-only jar')
        dex = z.read('extensions/youtube.mpe')
        for needle in (b'KhmerTtsClient', b'/api/process-multi', b'EqualizerPlayerButton',
                       b'EqualizerPatch', b'api.sea-lion.ai', b'aisingapore/Gemma-SEA-LION-v4-27B-IT',
                       b'PostImageDownloadPatch', b'PostTranslatePatch', b'CommentsSearchFilter',
                       b'NiconicoCommentsController'):
            check(needle in dex, f'Missing custom extension: {needle!r}')
    return {'sha256': digest, 'bytes': len(data), 'version': VERSION}


def verify_listing(text: str, include_experimental: bool) -> None:
    matches = list(re.finditer(r'^Name: (.+)$', text, flags=re.MULTILINE))
    names = [m.group(1).strip() for m in matches]
    check(len(names) == len(set(names)) and set(names) == expected_names(), 'Morphe selector listing differs')
    wanted = [v for v, _, experimental in TARGETS if include_experimental or not experimental]
    for i, match in enumerate(matches):
        block = text[match.start():matches[i+1].start() if i+1 < len(matches) else len(text)]
        packages = re.findall(r'^\s*Package name: (\S+)', block, flags=re.MULTILINE)
        check(not packages or packages == [PACKAGE], 'Unexpected package in Morphe listing: ' + names[i])
        if packages:
            versions = re.findall(r'^[ \t]*(\d+\.\d+\.\d+)[ \t]*$', block, flags=re.MULTILINE)
            check(set(versions) == set(wanted), 'Wrong versions in Morphe listing: ' + names[i])
    if not include_experimental:
        check('21.30.216' in text and '21.43.523' not in text and '21.42.241' not in text,
              'Default listing exposes an experimental version or lacks the requested stable version')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--mpp', type=Path)
    parser.add_argument('--listing', type=Path)
    parser.add_argument('--experimental-listing', type=Path)
    args = parser.parse_args()
    verify_catalog(json.loads(args.manifest.read_text(encoding='utf-8')))
    print('Verified: 110 YouTube + 5 generic selectors, default 21.30.216 (SDK 29)')
    if args.mpp:
        print('Verified MPP:', verify_archive(args.mpp))
    if args.listing:
        verify_listing(args.listing.read_text(), False)
        print('Verified Morphe default patch listing')
    if args.experimental_listing:
        verify_listing(args.experimental_listing.read_text(), True)
        print('Verified Morphe experimental patch listing')


if __name__ == '__main__':
    main()
