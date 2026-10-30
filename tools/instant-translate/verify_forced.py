#!/usr/bin/env python3
"""Validate CI-only fault injection; never ship the test APK or test patch."""
import argparse
import gc
import zipfile
from pathlib import Path

from inspect_apk import DEX_NAME, verify_asset
from verify_patched import inspect, verify_methods


def body(path: Path) -> list[tuple[str, str]]:
    from androguard.core.dex import DEX
    from loguru import logger
    logger.remove()
    found = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if not DEX_NAME.fullmatch(info.filename):
                continue
            dex = DEX(archive.read(info))
            for cls in dex.get_classes():
                if cls.get_name() != 'Lus9;':
                    continue
                for method in cls.get_methods():
                    if method.get_name() == 'G' and ''.join(method.get_descriptor().split()) == '(Lmx1;)Ljava/lang/Object;':
                        found.append([(item.get_name(), item.get_output()) for item in method.get_instructions()])
            del dex
            gc.collect()
    if len(found) != 1:
        raise ValueError('CI-only native failure injection target not unique')
    return found[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base', type=Path)
    parser.add_argument('forced', type=Path)
    args = parser.parse_args()
    verify_asset(args.base)
    verify_methods(inspect(args.base), inspect(args.forced))
    before, after = body(args.base), body(args.forced)
    if len(after) != len(before) + 2 or after[0][0] != 'const/4' or after[1][0] != 'return-object':
        raise ValueError('CI-only original-engine failure was not injected as expected')
    print('Verified production fallback hooks and isolated CI-only native failure')


if __name__ == '__main__':
    main()
