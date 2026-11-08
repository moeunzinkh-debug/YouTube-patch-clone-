#!/usr/bin/env python3
"""Prepare an isolated King-Patcher Morphe build without modifying any APK."""
from __future__ import annotations
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = '0.1.0-dev.1'

def prepare(destination: Path) -> None:
    destination = destination.resolve()
    if destination.exists() or destination == ROOT or ROOT in destination.parents:
        raise ValueError('Use a new temporary directory outside the repository')
    shutil.copytree(ROOT / 'tools/king-patcher/project', destination)
    for name in ('gradlew', 'gradlew.bat', 'build.gradle.kts'):
        shutil.copy2(ROOT / name, destination / name)
    shutil.copytree(ROOT / 'gradle', destination / 'gradle')
    wrapper = destination / 'gradle/wrapper/gradle-wrapper.properties'
    wrapper_text = wrapper.read_text().replace('networkTimeout=10000', 'networkTimeout=60000').replace('retries=0', 'retries=2')
    wrapper.write_text(wrapper_text)
    settings = (ROOT / 'settings.gradle.kts').read_text()
    marker = '// Include morphe-patcher as composite builds'
    if settings.count(marker) != 1 or settings.count('rootProject.name = "youtube-patch-clone"') != 1:
        raise ValueError('Unexpected root Gradle settings')
    settings = settings[:settings.index(marker)]
    settings = settings.replace('rootProject.name = "youtube-patch-clone"', 'rootProject.name = "king-patcher-patches"')
    settings = settings.replace('include(":patches:stub")', '')
    (destination / 'settings.gradle.kts').write_text(settings)
    shutil.copy2(ROOT / 'extensions/proguard-rules.pro', destination / 'extensions/proguard-rules.pro')
    (destination / 'gradle.properties').write_text(f'org.gradle.jvmargs=-Xmx2048M\nversion={VERSION}\nandroid.useAndroidX=true\n')
    print('Prepared isolated King-Patcher project:', destination)

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    prepare(args.destination)

if __name__ == '__main__':
    main()
