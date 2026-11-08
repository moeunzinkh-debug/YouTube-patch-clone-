#!/usr/bin/env python3
"""Inspect bounded method signatures needed to interoperate with the pinned APK."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from trace_menu import find_class, parse_class, scrub, windows

CLASSES = (
    'Lʽᐧ/ˉ;', 'Lʽٴ/ᵎ;', 'Lʽᐧ/ˊ$ʻ;', 'Lʽٴ/ᐧᐧ$ʽٴ;',
    'Lorg/jf/dexlib2/DexFileFactory;', 'Lorg/jf/dexlib2/Opcodes;',
    'Lorg/jf/dexlib2/rewriter/DexRewriter;', 'Lorg/jf/dexlib2/rewriter/RewriterModule;',
    'Lorg/jf/dexlib2/rewriter/MethodRewriter;', 'Lorg/jf/dexlib2/rewriter/Rewriter;',
    'Lorg/jf/dexlib2/iface/Method;', 'Lorg/jf/dexlib2/immutable/ImmutableMethod;',
    'Lorg/jf/dexlib2/immutable/ImmutableMethodImplementation;',
    'Lorg/jf/dexlib2/immutable/instruction/ImmutableInstruction21s;',
    'Lorg/jf/dexlib2/immutable/instruction/ImmutableInstruction35c;',
    'Lorg/jf/dexlib2/immutable/instruction/ImmutableInstruction10x;',
    'Lorg/jf/dexlib2/immutable/reference/ImmutableMethodReference;',
    'Lcom/android/apksig/ApkSigner$Builder;', 'Lcom/android/apksig/ApkSigner$SignerConfig$Builder;',
    'Lcom/android/apksig/ApkSigner;', 'Lcom/android/apksig/ApkVerifier;',
    'Lcom/android/apksig/ApkVerifier$Builder;', 'Lcom/android/apksig/ApkVerifier$Result;',
)
TRACE_BODIES = {'Lʽᐧ/ˉ;', 'Lʽٴ/ᵎ;', 'Lʽᐧ/ˊ$ʻ;', 'Lʽٴ/ᐧᐧ$ʽٴ;'}


def trace(decoded: Path) -> dict:
    result = {}
    for descriptor in CLASSES:
        path = find_class(decoded, descriptor)
        if path is None:
            result[descriptor] = {'found': False}
            continue
        header, methods = parse_class(path)
        item = {'found': True, 'header': [scrub(line) for line in header],
                'methods': {name: scrub(body[0]) for name, body in methods.items()}}
        if descriptor in TRACE_BODIES:
            item['selected_bodies'] = {
                name: windows(body, ('invoke-', 'iget', 'sget', 'iput', 'sput', 'return', 'new-instance'), radius=4)
                for name, body in methods.items()
                if name.startswith(('<init>(', 'onItemClick(', 'getItemId(', 'getItem('))
            }
        result[descriptor] = item
    return {'classes': result, 'note': 'Signatures and snippets only; string constants are redacted.'}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decoded', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = trace(args.decoded)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'classes_found': sum(c['found'] for c in result['classes'].values()),
                      'classes_total': len(result['classes'])}))


if __name__ == '__main__':
    main()
