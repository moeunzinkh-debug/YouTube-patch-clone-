#!/usr/bin/env python3
"""Trace pinned King-Patcher menu hooks from a disposable apktool decode.

Only bounded code identifiers, opcodes, resource IDs, and redacted snippets are
recorded. No APK is rewritten or distributed by this diagnostic.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TARGET_CLASS = 'Lʽٴ/ᐧᐧ;'
TARGET_METHODS = ('ˆʻ()V', 'ˆˎ()V', 'ˊᵎ(I)V')
RESOURCE_IDS = ('0x7f110141', '0x7f110104', '0x7f110144', '0x7f1100b2')
CLASS_DESCRIPTOR = re.compile(r'L[^\s,()]+;')
STR_LITERAL = re.compile(r'(const-string(?:/jumbo)?\s+[^,]+,\s+)"(?:\\.|[^"\\])*"')


def scrub(line: str) -> str:
    """Never copy string literals, which may contain paths or credentials."""
    return STR_LITERAL.sub(r'\1"<redacted>"', line.rstrip())[:500]


def find_class(decoded: Path, descriptor: str) -> Path | None:
    if not descriptor.startswith('L') or not descriptor.endswith(';'):
        return None
    name = descriptor[1:-1] + '.smali'
    for root in sorted(decoded.glob('smali*')):
        path = root / name
        if path.is_file():
            return path
    return None


def parse_class(path: Path) -> tuple[list[str], dict[str, list[str]]]:
    header, methods = [], {}
    current = None
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        stripped = line.strip()
        if stripped.startswith('.method '):
            current = stripped.split()[-1]
            methods[current] = [stripped]
        elif current is not None:
            methods[current].append(stripped)
            if stripped == '.end method':
                current = None
        elif stripped.startswith(('.class ', '.super ', '.implements ', '.field ')):
            header.append(stripped)
    return header[:200], methods


def windows(lines: list[str], needles: tuple[str, ...], radius: int = 32) -> dict:
    indexes = [index for index, line in enumerate(lines) if any(token in line.lower() for token in needles)]
    keep = set(range(min(20, len(lines)))) | set(range(max(0, len(lines) - 12), len(lines)))
    for index in indexes[:12]:
        keep.update(range(max(0, index - radius), min(len(lines), index + radius + 1)))
    selected = [{'line': i + 1, 'text': scrub(lines[i])} for i in sorted(keep)[:700]]
    return {'line_count': len(lines), 'matched_offsets': [x + 1 for x in indexes], 'lines': selected}


def callsites(decoded: Path, needles: tuple[str, ...]) -> list[dict]:
    result = []
    for root in sorted(decoded.glob('smali*')):
        for path in root.rglob('*.smali'):
            klass = method = None
            try:
                with path.open(encoding='utf-8', errors='replace') as stream:
                    for line in stream:
                        text = line.strip()
                        if text.startswith('.class '): klass = text.split()[-1]
                        elif text.startswith('.method '): method = text.split()[-1]
                        elif text == '.end method': method = None
                        if klass and method and any(needle in text for needle in needles):
                            result.append({'class': klass, 'method': method, 'instruction': scrub(text)})
            except OSError:
                continue
    return result[:100]


def trace(decoded: Path) -> dict:
    path = find_class(decoded, TARGET_CLASS)
    if path is None:
        raise ValueError('Pinned menu class was not found in the decoded APK')
    header, all_methods = parse_class(path)
    if any(method not in all_methods for method in TARGET_METHODS):
        raise ValueError('Pinned menu methods were not found')
    methods = {method: windows(all_methods[method], RESOURCE_IDS) for method in TARGET_METHODS}
    references = set()
    for details in methods.values():
        for entry in details['lines']:
            if 'new-instance' in entry['text'] or 'invoke-direct' in entry['text']:
                references.update(match for match in CLASS_DESCRIPTOR.findall(entry['text'])
                                  if match.startswith('Lʽٴ/') and match != TARGET_CLASS)
    callbacks = {}
    for descriptor in sorted(references)[:40]:
        candidate = find_class(decoded, descriptor)
        if candidate is None:
            continue
        class_header, class_methods = parse_class(candidate)
        picked = {}
        for name, body in class_methods.items():
            if name.startswith(('onClick(', 'onItemClick(', '<init>(')):
                # First/last lines plus all invoke instructions, bounded.
                relevant = tuple(set(RESOURCE_IDS) | {'invoke-', 'const', 'iget', 'sget', 'iput', 'sput'})
                picked[name] = windows(body, relevant, radius=3)
        if picked:
            callbacks[descriptor] = {'header': [scrub(line) for line in class_header], 'methods': picked}
    needles = tuple(TARGET_CLASS + '->' + method for method in TARGET_METHODS)
    return {'target_class': TARGET_CLASS, 'class_header': [scrub(line) for line in header],
            'methods': methods, 'callsites': callsites(decoded, needles),
            'nearby_callback_classes': callbacks,
            'note': 'Static bytecode snippets are redacted and do not prove runtime behavior.'}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decoded', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = trace(args.decoded)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'target': result['target_class'],
                      'methods': {name: data['line_count'] for name, data in result['methods'].items()},
                      'callsites': len(result['callsites']),
                      'nearby_callback_classes': len(result['nearby_callback_classes'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
