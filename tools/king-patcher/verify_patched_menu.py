#!/usr/bin/env python3
"""Verify injected menu model arguments and dispatch in a disposable decoded APK."""
from __future__ import annotations
import argparse
import re
from pathlib import Path
from trace_menu import find_class, parse_class

TARGET = 'Lʽٴ/ᐧᐧ;'
MODEL = 'Lʽᐧ/ˉ;'
ITEMS = {
    0x7e4d0001: ('Remove license (Google Play LVL)', 'New classic LVL method; selected APK only'),
    0x7e4d0002: ('Remove insignificant things', 'Choose compiled layout elements to hide'),
}

def instructions(body: list[str]) -> list[str]:
    return [line.strip() for line in body if line.strip() and not line.strip().startswith(('.', ':', '#'))]

def verify(decoded: Path, modes: set[int]) -> None:
    path = find_class(decoded, TARGET)
    if path is None: raise ValueError('Patched King fragment missing')
    _, methods = parse_class(path)
    for name, listing, scratch in [('ˆʻ()V', 0, 1), ('ˆˎ()V', 2, 3)]:
        lines = instructions(methods[name])
        for marker, (title, description) in ITEMS.items():
            hits = [i for i, line in enumerate(lines) if re.match(rf'const\s+v{scratch + 1},\s+0x{marker:x}$', line)]
            if len(hits) != (1 if marker in modes else 0): raise ValueError(f'{name}: unexpected {marker:x} count')
            if not hits: continue
            i = hits[0]
            expected = [
                f'new-instance v{scratch}, {MODEL}',
                f'const v{scratch+1}, 0x{marker:x}',
                f'const-string v{scratch+2}, "{title}"',
                f'const/4 v{scratch+3}, 0x0',
                f'const-string v{scratch+4}, "{description}"',
                f'const-string v{scratch+5}, "#FFFFFF"',
                f'const v{scratch+6}, 0x7f080083',
                f'invoke-direct/range {{v{scratch} .. v{scratch+6}}}, {MODEL}-><init>(ILjava/lang/String;ILjava/lang/String;Ljava/lang/String;I)V',
                f'invoke-virtual {{v{listing}, v{scratch}}}, Ljava/util/ArrayList;->add(Ljava/lang/Object;)Z',
            ]
            if lines[i-1:i+8] != expected:
                raise ValueError(f'{name}: menu constructor argument sequence changed')
    dispatch = instructions(methods['ˊᵎ(I)V'])
    if not dispatch or dispatch[0] != 'sget-object v0, Lʽٴ/ᐧᐧ;->ʼﹶ:Lru/jgaiecip/osuojvyxe/MainActivity;':
        raise ValueError('Dispatcher does not use the inspected host Activity field')
    if not any('Lapp/morphe/extension/king/MenuBridge;->handle(Landroid/app/Activity;I)Z' in line for line in dispatch[:10]):
        raise ValueError('Dispatcher bridge missing')
    if find_class(decoded, 'Lapp/morphe/extension/king/ToolFragment;') is None:
        raise ValueError('Tool fragment missing')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decoded', type=Path)
    parser.add_argument('mode', choices=('lvl', 'ui', 'both'))
    args = parser.parse_args()
    modes = {marker for marker in ITEMS if args.mode == 'both' or (args.mode == 'lvl') == (marker == 0x7e4d0001)}
    verify(args.decoded, modes)
    print(f'Verified {args.mode} menu IDs, raw labels, valid color strings and dispatcher')

if __name__ == '__main__':
    main()
