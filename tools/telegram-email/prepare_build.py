#!/usr/bin/env python3
"""Prepare an isolated Telegram-only experiment without altering the stable bundle/vendor."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/telegram'))
import prepare_build as stable  # noqa: E402

VERSION = '1.23.1-tg.email-exp.1'
OVERLAY = ROOT / 'extras/telegram-email-experiment'


def prepare(dest: Path) -> None:
    stable.prepare(dest)
    for part in ('patches', 'extensions'):
        source = OVERLAY / part
        for item in source.rglob('*'):
            if item.is_file():
                relative = item.relative_to(OVERLAY)
                target = dest / relative
                if target.exists():
                    raise ValueError(f'Experiment must not replace upstream files: {relative}')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
    properties = dest / 'gradle.properties'
    original = properties.read_text(encoding='utf-8')
    expected = 'version = ' + stable.FORK_VERSION
    if original.count(expected) != 1:
        raise ValueError('Unexpected stable build version')
    properties.write_text(original.replace(expected, 'version = ' + VERSION), encoding='utf-8')
    patch_build = dest / 'patches/build.gradle.kts'
    original = patch_build.read_text(encoding='utf-8')
    original = original.replace('name = "Telegram Patch Clone"', 'name = "Telegram Patch Clone - Email Experiment"')
    original = original.replace('Telegram-only subset of rushiranpise patches v1.23.1; modified build.',
                                'Telegram-only upstream subset plus an opt-in experimental email alternative.')
    patch_build.write_text(original, encoding='utf-8')
    print('Prepared opt-in email experiment at', dest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    prepare(args.destination.resolve())


if __name__ == '__main__':
    main()
