#!/usr/bin/env python3
"""Emit small redacted method traces for the exact inspected King menu integration."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from trace_menu import find_class, parse_class, scrub

TARGETS = {
    'Lʽᐧ/ˉ;': ('<init>(IILjava/lang/String;I)V', '<init>(ILjava/lang/String;Z)V',
                 '<init>(ILjava/lang/String;ILjava/lang/String;Ljava/lang/String;I)V'),
    'Lʽᐧ/ˊ;': ('getView(ILandroid/view/View;Landroid/view/ViewGroup;)Landroid/view/View;',),
    'Lʽᐧ/ˊ$ʻ;': ('onItemClick(Landroid/widget/AdapterView;Landroid/view/View;IJ)V',),
    'Lʽٴ/ᐧᐧ;': ('ˆʻ()V', 'ˆˎ()V', 'ˊᵎ(I)V'),
    'Lru/jgaiecip/osuojvyxe/MainActivity;': ('onActivityResult(IILandroid/content/Intent;)V',
                                              'onCreate(Landroid/os/Bundle;)V'),
    'Lʽᐧ/ʽ;': ('ʾʾ(Ljava/util/ArrayList;Z)V', 'ʿʿ(Ljava/lang/String;Ljava/util/ArrayList;Z)V'),
}

def trace(decoded: Path) -> dict:
    report = {}
    for descriptor, names in TARGETS.items():
        path = find_class(decoded, descriptor)
        if path is None:
            report[descriptor] = {'found': False}
            continue
        header, methods = parse_class(path)
        selected = {}
        for name in names:
            body = methods.get(name)
            if body is None:
                selected[name] = None
                continue
            cleaned = [scrub(line) for line in body if line.strip() and not line.strip().startswith(('.line ', '.local ', '.end local ', '.restart local ', '.prologue'))]
            if name == 'ˊᵎ(I)V':
                cleaned = cleaned[:100]
            elif name in ('ˆʻ()V', 'ˆˎ()V'):
                cleaned = cleaned[:100] + ['<omitted>'] + cleaned[-70:]
            elif name in ('ʾʾ(Ljava/util/ArrayList;Z)V', 'ʿʿ(Ljava/lang/String;Ljava/util/ArrayList;Z)V'):
                indices = {i for i, line in enumerate(cleaned) if any(token in line for token in
                           ('Lʽᐧ/ˉ;->', 'Landroid/widget/ArrayAdapter;', 'getItem(', 'setText(', 'onItemClick('))}
                keep = set(range(min(20, len(cleaned))))
                for i in sorted(indices)[:50]: keep.update(range(max(0, i - 5), min(len(cleaned), i + 6)))
                cleaned = [f'{i + 1}: {cleaned[i]}' for i in sorted(keep)[:400]]
            elif len(cleaned) > 400:
                cleaned = cleaned[:400]
            selected[name] = cleaned
        report[descriptor] = {'found': True, 'header': [scrub(line) for line in header], 'methods': selected}
    return {'classes': report, 'note': 'String literals are redacted; static trace only.'}

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decoded', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = trace(args.decoded)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'classes_found': sum(c['found'] for c in result['classes'].values())}))

if __name__ == '__main__':
    main()
