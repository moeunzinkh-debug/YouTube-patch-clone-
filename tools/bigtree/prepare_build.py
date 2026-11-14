#!/usr/bin/env python3
"""Prepare an isolated BigTree Morphe build without other app patches."""
from __future__ import annotations
import shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = '0.1.0-dev.14'

def prepare(dest: Path) -> None:
    dest = dest.resolve()
    if dest.exists() or dest == ROOT or ROOT in dest.parents:
        raise ValueError('Use a new temporary build directory outside the repository')
    shutil.copytree(ROOT / 'tools/bigtree/project', dest)
    for name in ('gradlew', 'gradlew.bat', 'build.gradle.kts'):
        shutil.copy2(ROOT / name, dest / name)
    shutil.copytree(ROOT / 'gradle', dest / 'gradle')
    settings = (ROOT / 'settings.gradle.kts').read_text()
    marker = '// Include morphe-patcher as composite builds'
    if settings.count(marker) != 1 or settings.count('rootProject.name = "youtube-patch-clone"') != 1:
        raise ValueError('Unexpected root Gradle settings')
    settings = settings[:settings.index(marker)]
    settings = settings.replace('rootProject.name = "youtube-patch-clone"', 'rootProject.name = "bigtree-patches"')
    settings = settings.replace('include(":patches:stub")', '')
    (dest / 'settings.gradle.kts').write_text(settings)
    (dest / 'extensions').mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'extensions/proguard-rules.pro', dest / 'extensions/proguard-rules.pro')
    (dest / 'gradle.properties').write_text(
        f'org.gradle.jvmargs=-Xmx2048M\nversion={VERSION}\nandroid.useAndroidX=true\n'
    )

def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit('usage: prepare_build.py DESTINATION')
    prepare(Path(sys.argv[1]))
    print('Prepared isolated BigTree project:', sys.argv[1])

if __name__ == '__main__':
    main()
