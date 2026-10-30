#!/usr/bin/env python3
"""Prepare an isolated Kimi Morphe build, without modifying other app bundles."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = '0.1.0-dev.1'


def prepare(dest: Path) -> None:
    dest = dest.resolve()
    if dest.exists() or dest == ROOT or ROOT in dest.parents:
        raise ValueError('Use a new temporary build directory outside the repository')
    shutil.copytree(ROOT / 'tools/kimi/project', dest)
    for name in ('gradlew', 'gradlew.bat', 'build.gradle.kts'):
        shutil.copy2(ROOT / name, dest / name)
    shutil.copytree(ROOT / 'gradle', dest / 'gradle')
    settings = (ROOT / 'settings.gradle.kts').read_text()
    marker = '// Include morphe-patcher as composite builds'
    if settings.count(marker) != 1 or settings.count('rootProject.name = "youtube-patch-clone"') != 1:
        raise ValueError('Unexpected root Gradle settings')
    settings = settings[:settings.index(marker)]
    settings = settings.replace('rootProject.name = "youtube-patch-clone"', 'rootProject.name = "kimi-patches"')
    settings = settings.replace('include(":patches:stub")', '')
    (dest / 'settings.gradle.kts').write_text(settings)
    (dest / 'extensions').mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'extensions/proguard-rules.pro', dest / 'extensions/proguard-rules.pro')
    (dest / 'gradle.properties').write_text(f'org.gradle.jvmargs=-Xmx2048M\nversion={VERSION}\nandroid.useAndroidX=true\n')
    print('Prepared isolated Kimi project:', dest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    prepare(args.destination)


if __name__ == '__main__':
    main()
