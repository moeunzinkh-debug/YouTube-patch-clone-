#!/usr/bin/env python3
"""Build a Telegram-only project from the pinned, verbatim upstream source subset.

The copied Telegram patch files and shared runtime behavior remain unchanged.
Generic dependencies are made anonymous in the temporary build so they do not
become selectable patches for unrelated apps. The generated project is not a
byte-for-byte copy of upstream's multi-app release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / 'extras/telegram-upstream'
SOURCE_MANIFEST_SHA256 = 'ebae1481f4e4a4f5af5c704e612a4b7eacd95c52d8f2247d9b6728f825caa682'
UPSTREAM_COMMIT = '92c0fca0ae103a419c7fc61f9c5b8b38b7d6b82a'
FORK_VERSION = '1.23.1-tg.1'

PATCH_BUILD = '''group = "app.telegram.patchclone"

patches {
    about {
        name = "Telegram Patch Clone"
        description = "Telegram-only subset of rushiranpise patches v1.23.1; modified build."
        source = "https://github.com/moeunzinkh-debug/YouTube-patch-clone-"
        author = "rushiranpise; YouTube Patch Clone contributors"
        contact = "https://github.com/moeunzinkh-debug/YouTube-patch-clone-"
        website = "https://github.com/moeunzinkh-debug/YouTube-patch-clone-"
        license = "GPLv3"
    }
}

kotlin { compilerOptions { freeCompilerArgs.add("-Xcontext-parameters") } }
'''

EXTENSION_BUILD = '''extension { name = "extensions/extension.mpe" }

android {
    namespace = "app.template.extension"
    buildFeatures { buildConfig = false }
    lint { abortOnError = false; checkReleaseBuilds = false }
}

dependencies { implementation("org.lsposed.hiddenapibypass:hiddenapibypass:4.3") }
'''

DEPENDENCY_HEADERS = {
    'patches/src/main/kotlin/app/template/patches/shared/cert/CertExtractor.kt':
        ('extractApkCertificatePatch', 'rawResourcePatch'),
    'patches/src/main/kotlin/app/template/patches/shared/firebase/SpoofFirebaseCertHashPatch.kt':
        ('spoofFirebaseCertHashPatch', 'bytecodePatch'),
    'patches/src/main/kotlin/app/template/patches/shared/installer/SpoofInstallSourcePatch.kt':
        ('spoofInstallSourcePatch', 'bytecodePatch'),
    'patches/src/main/kotlin/app/template/patches/shared/signature/SpoofSignatureVerificationPatch.kt':
        ('spoofSignatureVerificationPatch', 'bytecodePatch'),
}


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def verify_vendor() -> dict:
    path = VENDOR / 'upstream-source-manifest.json'
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCE_MANIFEST_SHA256:
        raise ValueError('Upstream source manifest changed; re-audit the pinned source')
    metadata = json.loads(data)
    if metadata['commit'] != UPSTREAM_COMMIT or metadata['tag'] != 'v1.23.1':
        raise ValueError('Unexpected upstream pin')
    files = metadata['files']
    actual = {str(p.relative_to(VENDOR)) for p in VENDOR.rglob('*') if p.is_file()}
    if actual != set(files) | {'upstream-source-manifest.json'}:
        raise ValueError('Unexpected or missing vendored file')
    for name, info in files.items():
        source = VENDOR / name
        if source.is_symlink() or git_blob(source.read_bytes()) != info['git_blob']:
            raise ValueError('Upstream file differs from pinned git blob: ' + name)
    return metadata


def telegram_constants(original: str) -> str:
    start_marker = 'val TELEGRAM_COMPATIBILITY = Compatibility('
    end_marker = 'val THE_ATHLETIC_COMPATIBILITY = Compatibility('
    if original.count(start_marker) != 1 or original.count(end_marker) != 1:
        raise ValueError('Upstream compatibility block changed')
    block = original[original.index(start_marker):original.index(end_marker)].rstrip()
    names = re.findall(r'^val (\w+_COMPATIBILITY)\s*=', block, re.MULTILINE)
    if names != ['TELEGRAM_COMPATIBILITY', 'TELEGRAM_PLUS_COMPATIBILITY', 'TELEGRAM_WEB_COMPATIBILITY']:
        raise ValueError('Unexpected compatibility entries in Telegram block')
    return ('// Telegram-only excerpt of upstream Constants.kt; see extras/telegram-upstream/LICENSE.\n'
            'package app.template.patches.shared\n\n'
            'import app.morphe.patcher.patch.ApkFileType\n'
            'import app.morphe.patcher.patch.AppTarget\n'
            'import app.morphe.patcher.patch.Compatibility\n\n'
            'object Constants {\n\n' + block + '\n}\n')


def hide_generic_selector(original: str, symbol: str, kind: str) -> str:
    head = f'val {symbol} = {kind}('
    if original.count(head) != 1:
        raise ValueError('Upstream dependency declaration changed: ' + symbol)
    start = original.index(head)
    end = original.find('\n) {', start)
    if end < 0:
        raise ValueError('Cannot find dependency declaration end: ' + symbol)
    old = original[start:end + len('\n) {')]
    if 'name = ' not in old or 'default = false' not in old:
        raise ValueError('Unexpected shared selector header: ' + symbol)
    return original[:start] + f'val {symbol} = {kind}(default = false) {{' + original[end + len('\n) {'):]


def prepare(dest: Path) -> None:
    verify_vendor()
    if dest.exists():
        raise ValueError('Use a new temporary build directory')
    if dest == ROOT or ROOT in dest.parents:
        raise ValueError('Build outside the repository to keep the subset isolated')
    shutil.copytree(VENDOR, dest)
    (dest / 'upstream-source-manifest.json').unlink()
    path = dest / 'patches/src/main/kotlin/app/template/patches/shared/Constants.kt'
    path.write_text(telegram_constants(path.read_text(encoding='utf-8')), encoding='utf-8')
    for filename, (symbol, kind) in DEPENDENCY_HEADERS.items():
        path = dest / filename
        path.write_text(hide_generic_selector(path.read_text(encoding='utf-8'), symbol, kind), encoding='utf-8')
    (dest / 'patches/build.gradle.kts').write_text(PATCH_BUILD, encoding='utf-8')
    (dest / 'extensions/extension/build.gradle.kts').write_text(EXTENSION_BUILD, encoding='utf-8')
    path = dest / 'settings.gradle.kts'
    settings = path.read_text(encoding='utf-8')
    if settings.count('rootProject.name = "morphe-patches"') != 1:
        raise ValueError('Unexpected upstream settings')
    path.write_text(settings.replace('rootProject.name = "morphe-patches"',
                                     'rootProject.name = "telegram-patch-clone"'), encoding='utf-8')
    path = dest / 'gradle.properties'
    properties = path.read_text(encoding='utf-8')
    if properties.count('version = 1.23.1') != 1:
        raise ValueError('Unexpected upstream project version')
    path.write_text(properties.replace('version = 1.23.1', 'version = ' + FORK_VERSION), encoding='utf-8')
    print('Prepared isolated Telegram-only source project at', dest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    prepare(args.destination.resolve())


if __name__ == '__main__':
    main()
