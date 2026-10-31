#!/usr/bin/env python3
"""Safely replace only Instant Translate's two bundle assets in the existing prerelease.

The new bundle is uploaded under temporary names, verified, then promoted. The
previous assets are retained until promotion and release notes have succeeded.
APK assets are neither downloaded nor modified. A failure before completion
attempts to restore the previous asset names and original release notes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

REPO = 'moeunzinkh-debug/YouTube-patch-clone-'
RELEASE_ID = 429093150
TAG = 'Instant-translate'
VERSION = '0.4.0-dev.1'
NEW_BUNDLE_SHA = '45e5895edbdf1826fc3c0fbfb3c6d82ee867cde645a52b3670d0590f987a30db'
NEW_CHECKSUM_SHA = '9c071377dcf23d564897fcb8348798bb31bf6e33acff9c6c13b10c48c26e4f38'
OLD = {
    'bundle.mpp': ('4fe99fee6a9ea32887fdb00c694dbb3b2685424dcbe1cff0b4bb770d03ede859', 50062),
    'bundle.mpp.sha256': ('189e189e4f6ed3c800779f78e14a4bf6b0da42ed0f36d619efc4467e79d06c5c', 77),
}
NEW = {'bundle.mpp': NEW_BUNDLE_SHA, 'bundle.mpp.sha256': NEW_CHECKSUM_SHA}
OLD_IDS = {'bundle.mpp': 693851131, 'bundle.mpp.sha256': 693851166}
# Pinned metadata only: the release APKs are never read or altered by this tool.
EXPECTED_APKS = {
    'base.apk': (693913094, '8cf8c697d2ce04350d2a7fc7d301751e8bb30cf98f298d288ba8b9bfe3f7b1b2'),
    'split_config.arm64_v8a.apk': (693928331, 'b52f61095730550b1e38c8a3a6bc687261d8eb806ec14012ff765a950bb7d899'),
    'split_config.en.apk': (693928290, '8532ec7afd66f4f5bfe53fd357bc7afdec45f2d2eff4ce50f347bb403bd5c84f'),
    'split_config.km.apk': (693928245, '4ab8bba827d2d393b5e92bcc5f74bae80da322e970d39118f9c7ed5ea0c11cad'),
    'split_config.xxhdpi.apk': (693928085, '4ffa280a432c5848a1db1649ab2528f7ccdbc9d1b50099ff8677e59cf9fb7efd'),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assets_by_name(release: dict) -> dict[str, dict]:
    assets = release.get('assets', [])
    names = {asset['name']: asset for asset in assets}
    if len(names) != len(assets):
        raise ValueError('Duplicate asset names')
    return names


def verify_release(release: dict) -> dict[str, dict]:
    if (release.get('id') != RELEASE_ID or release.get('tag_name') != TAG or
            release.get('draft') or not release.get('prerelease')):
        raise ValueError('Unexpected release identity or state')
    assets = assets_by_name(release)
    for name, (asset_id, digest) in EXPECTED_APKS.items():
        item = assets.get(name)
        if not item or item.get('id') != asset_id or item.get('digest') != 'sha256:' + digest:
            raise ValueError('Release APK metadata changed: ' + name)
    return assets


def check_asset(asset: dict | None, digest: str, size: int | None = None) -> None:
    if (not asset or asset.get('state') != 'uploaded' or asset.get('digest') != 'sha256:' + digest or
            (size is not None and asset.get('size') != size)):
        raise ValueError('Missing or unexpected asset: ' + (asset or {}).get('name', '<missing>'))


def unchanged_assets(release: dict, excluded_ids: set[int]) -> dict[int, tuple]:
    return {a['id']: (a['name'], a.get('size'), a.get('digest'), a.get('state'))
            for a in release.get('assets', []) if a['id'] not in excluded_ids}


def release_notes(old_body: str) -> str:
    return f'''## ⚠️ Experimental Instant Translate bundle {VERSION}

**មិនទាន់បញ្ជាក់ runtime:** មិនបាន patch/install APK ឬសាកការបកប្រែពិត, premium features ឬ microG login សម្រាប់ bundle នេះទេ។ សូមកុំ uninstall app ដើម ឬបញ្ចូលព័ត៌មានឯកជនក្នុង APK ដែលមិនទាន់ទុកចិត្ត។

- `bundle.mpp` គឺជា Morphe Manager local patch source មិនមែន APK។ Release បច្ចុប្បន្នគឺ Instant Translate **v7.5.00307 (50350)**; SEA-LION selectors ក៏រាយកំណែចាស់ v7.5.00300។
- Google translation fallback ត្រូវបានដកចេញពី bundle។ **Original only** ជាលំនាំដើម; SEA-LION ត្រូវជ្រើសដោយខ្លួនឯង និងត្រូវការ API key។ វាមិនលុប Google services ដែល app ដើមប្រើ។
- SEA-LION: URL `https://api.sea-lion.ai/v1/`, model `aisingapore/Gemma-SEA-LION-v4-27B-IT`។ ពេលបើក fallback អត្ថបទដែលបរាជ័យ និង key ត្រូវបញ្ជូនទៅ HTTPS host ដែលអ្នកកំណត់។ ការគ្របដណ្ដប់គ្រប់ផ្នែក និង model access មិនទាន់បញ្ជាក់។
- `Remove license check` បិទ PairIP entry points ខាង client សម្រាប់ 50350 និងបន្ថយការការពារ license/integrity។ `Unlock premium local gate` ប្ដូរតែ local gate មិនបង្កើត subscription ឬធានាមុខងារខាង server។
- `Official microG service visibility` បន្ថែម package visibility ប៉ុណ្ណោះ; ត្រូវដំឡើង official microG និងគាំទ្រ signature spoofing ដាច់ដោយឡែក។ Login និង API compatibility មិនទាន់បានសាក។
- ការសាក build ឆ្លង 16 offline unit tests និង Morphe Desktop patch listing ប៉ុណ្ណោះ។ Crash ចាស់នៅ `LicenseActivity.verifyIntegrity` ជារបាយការណ៍សម្រាប់ 50342/bundle ចាស់; មិនទាន់ដឹង runtime របស់ 50350។
- Bundle SHA-256: `{NEW_BUNDLE_SHA}`។ APK ក្នុង release មិនបានកែ ឬជំនួស។

[ប្រភព patches](https://github.com/{REPO}/tree/main/tools/instant-translate) · [Merged PR #21](https://github.com/{REPO}/pull/21)

<details>
<summary>ប្រវត្តិ bundle ចាស់ 0.2.0-dev.1 (មាន Google fallback; មិនមែន bundle ខាងលើ)</summary>

{old_body.rstrip()}

</details>
'''


class GitHub:
    def __init__(self, temp: Path):
        self.temp = temp

    def command(self, *args: str) -> str:
        result = subprocess.run(['gh', *args], text=True, capture_output=True)
        if result.returncode:
            raise RuntimeError(f"gh {args[0]} failed ({result.returncode}): {result.stderr.strip()}")
        return result.stdout

    def release(self) -> dict:
        return json.loads(self.command('api', f'repos/{REPO}/releases/{RELEASE_ID}'))

    def upload(self, files: list[Path]) -> None:
        self.command('release', 'upload', TAG, *(str(f) for f in files), '--repo', REPO)

    def rename(self, asset_id: int, name: str) -> None:
        self.command('api', '--method', 'PATCH', f'repos/{REPO}/releases/assets/{asset_id}', '-f', 'name=' + name)

    def delete(self, asset_id: int) -> None:
        self.command('api', '--method', 'DELETE', f'repos/{REPO}/releases/assets/{asset_id}')

    def download(self, names: list[str], directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        args = ['release', 'download', TAG, '--repo', REPO, '--dir', str(directory)]
        for name in names: args += ['--pattern', name]
        self.command(*args)

    def update_body(self, body: str) -> None:
        path = self.temp / 'instant-release-notes.md'
        path.write_text(body)
        self.command('api', '--method', 'PATCH', f'repos/{REPO}/releases/{RELEASE_ID}', '-F', 'body=@' + str(path))


def publish(github: GitHub, bundle: Path, checksum: Path, temp: Path, run_id: str) -> dict:
    if not run_id.isdigit(): raise ValueError('Unexpected run ID')
    for name, path in (('bundle.mpp', bundle), ('bundle.mpp.sha256', checksum)):
        if sha(path) != NEW[name]: raise ValueError('Local artifact digest changed: ' + name)
    if checksum.read_text() != NEW_BUNDLE_SHA + '  bundle.mpp\n':
        raise ValueError('Unexpected checksum-file contents')

    before = github.release()
    assets = verify_release(before)
    previous = {name: assets.get(name) for name in OLD}
    for name, (digest, size) in OLD.items():
        check_asset(previous[name], digest, size)
        if previous[name]['id'] != OLD_IDS[name]:
            raise ValueError('Unexpected original bundle asset ID: ' + name)
    old_ids = {previous[name]['id'] for name in OLD}
    stable = unchanged_assets(before, old_ids)
    old_body = before.get('body') or ''
    staged_names = {name: f'stage-{VERSION}-{run_id}-{name}' for name in NEW}
    backup_names = {name: f'backup-0.2.0-dev.1-{run_id}-{name}' for name in OLD}
    if any(name in assets for name in [*staged_names.values(), *backup_names.values()]):
        raise ValueError('Temporary asset name collision')
    files = []
    temp.mkdir(parents=True, exist_ok=True)
    for name, source in (('bundle.mpp', bundle), ('bundle.mpp.sha256', checksum)):
        destination = temp / staged_names[name]
        shutil.copy2(source, destination)
        files.append(destination)

    new_ids: dict[str, int] = {}
    notes_attempted = False
    new_body = release_notes(old_body)
    try:
        github.upload(files)
        staged_release = github.release()
        staged = verify_release(staged_release)
        for name, digest in NEW.items():
            item = staged.get(staged_names[name])
            check_asset(item, digest, (bundle if name == 'bundle.mpp' else checksum).stat().st_size)
            new_ids[name] = item['id']
        if unchanged_assets(staged_release, old_ids | set(new_ids.values())) != stable:
            raise ValueError('Other release assets changed during staging')
        if (staged_release.get('body') or '') != old_body:
            raise ValueError('Release notes changed during staging')
        for name in OLD:
            check_asset(staged.get(name), *OLD[name])
            if staged[name]['id'] != previous[name]['id']:
                raise ValueError('Original bundle asset changed during staging')

        downloads = temp / 'verify-download'
        github.download(list(staged_names.values()), downloads)
        for name, stage_name in staged_names.items():
            if sha(downloads / stage_name) != NEW[name]:
                raise ValueError('Downloaded staged artifact failed verification: ' + name)
        if (downloads / staged_names['bundle.mpp.sha256']).read_text() != NEW_BUNDLE_SHA + '  bundle.mpp\n':
            raise ValueError('Downloaded checksum file differs')

        for name in OLD:
            github.rename(previous[name]['id'], backup_names[name])
        for name in NEW:
            github.rename(new_ids[name], name)

        promoted = github.release()
        current = verify_release(promoted)
        for name, digest in NEW.items():
            check_asset(current.get(name), digest)
            if current[name]['id'] != new_ids[name]:
                raise ValueError('Unexpected promoted asset ID: ' + name)
        if unchanged_assets(promoted, old_ids | set(new_ids.values())) != stable:
            raise ValueError('Other release assets changed during promotion')
        promoted_downloads = temp / 'verify-promoted-download'
        github.download(list(NEW), promoted_downloads)
        for name, digest in NEW.items():
            if sha(promoted_downloads / name) != digest:
                raise ValueError('Downloaded promoted artifact failed verification: ' + name)
        fresh = github.release()
        fresh_assets = verify_release(fresh)
        if (fresh.get('body') or '') != old_body:
            raise ValueError('Release notes changed during promotion')
        for name, digest in NEW.items():
            check_asset(fresh_assets.get(name), digest)
            if fresh_assets[name]['id'] != new_ids[name]:
                raise ValueError('Promoted asset changed before notes update')
        if unchanged_assets(fresh, old_ids | set(new_ids.values())) != stable:
            raise ValueError('Other release assets changed before notes update')
        notes_attempted = True
        github.update_body(new_body)
        after_notes = github.release()
        verified = verify_release(after_notes)
        if (after_notes.get('body') or '') != new_body:
            raise ValueError('Published release notes differ')
        for name, digest in NEW.items(): check_asset(verified.get(name), digest)
        if unchanged_assets(after_notes, old_ids | set(new_ids.values())) != stable:
            raise ValueError('Other release assets changed after promotion')
    except Exception:
        # Restore only names/notes that this run still owns; never touch APKs.
        try:
            current_release = github.release()
            current = assets_by_name(current_release)
            if notes_attempted and (current_release.get('body') or '') == new_body:
                github.update_body(old_body)
            for name, new_id in new_ids.items():
                if current.get(name, {}).get('id') == new_id:
                    github.rename(new_id, staged_names[name])
            current = assets_by_name(github.release())
            for name in OLD:
                if current.get(backup_names[name], {}).get('id') == previous[name]['id']:
                    github.rename(previous[name]['id'], name)
            current = assets_by_name(github.release())
            for name, stage_name in staged_names.items():
                item = current.get(stage_name)
                if item and item.get('digest') == 'sha256:' + NEW[name]: github.delete(item['id'])
        except Exception as rollback_error:
            print('::error::Rollback needs manual attention: ' + str(rollback_error))
        raise

    # Promotion and notes are verified. Remove only the two old bundle assets.
    for name in OLD:
        current = assets_by_name(github.release())
        backup = current.get(backup_names[name])
        if not backup or backup.get('id') != previous[name]['id']:
            raise ValueError('Old bundle backup changed before cleanup')
        check_asset(backup, *OLD[name])
        github.delete(backup['id'])

    final = github.release()
    final_assets = verify_release(final)
    for name, digest in NEW.items():
        item = final_assets.get(name)
        check_asset(item, digest)
        if item['id'] != new_ids[name]: raise ValueError('Unexpected final bundle asset ID')
    if unchanged_assets(final, set(new_ids.values())) != stable:
        raise ValueError('Non-bundle release assets changed')
    return {'status': 'published_and_verified', 'release_id': RELEASE_ID, 'tag': TAG,
            'version': VERSION, 'bundle_sha256': NEW_BUNDLE_SHA,
            'checksum_sha256': NEW_CHECKSUM_SHA, 'bundle_asset_id': new_ids['bundle.mpp'],
            'checksum_asset_id': new_ids['bundle.mpp.sha256'], 'apk_assets_modified': False,
            'app_installed_or_run': False, 'other_assets_unchanged': True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--checksum', type=Path, required=True)
    parser.add_argument('--temp', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if (os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('GITHUB_REPOSITORY') != REPO or
            os.environ.get('GITHUB_REF_NAME') != 'arena/a54bcff2-youtube-patch-clone'):
        raise SystemExit('Publication is allowed only in the explicitly selected CI branch/repository')
    result = publish(GitHub(args.temp), args.bundle, args.checksum, args.temp, os.environ['GITHUB_RUN_ID'])
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print('::notice::Instant Translate 0.4.0-dev.1 bundle and checksum published; APK assets unchanged.')


if __name__ == '__main__': main()
