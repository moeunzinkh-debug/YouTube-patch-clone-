#!/usr/bin/env python3
"""Emit a bounded, redacted DEX trace for toolbar interoperability research.

The inspected APK is a pinned third-party test fixture; no APK/DEX or user text
is written to the repository. Only a small allowlist of public UI tokens is
shown; all other string constants are redacted.
"""
from __future__ import annotations
import base64
import gzip
import re
import sys
import zipfile
from loguru import logger
from androguard.core.dex import DEX

logger.remove()
DEX_NAME = re.compile(r'classes(?:[2-9]|[1-9][0-9]+)?\.dex\Z')
TARGETS = {'Lmwv;', 'Lmtr;', 'Lmtm;', 'Lmvg;', 'Lmyc;', 'Lklo;', 'Lhcl;'}
UI_TOKENS = {'translate', 'translation', 'google_translate', 'translate_access_point',
             'translator', 'translation_keyboard', 'translate_keyboard'}


def render(dex, method):
    lines = []
    for offset, instruction in method.get_instructions_idx():
        op = instruction.get_name()
        text = instruction.get_output()
        if op in ('const-string', 'const-string/jumbo'):
            value = dex.get_cm_string(instruction.get_ref_kind())
            text = text.split(',', 1)[0] + ', ' + (repr(value) if value.lower() in UI_TOKENS else '<redacted>')
        elif '"' in text or 'http:' in text.lower() or 'https:' in text.lower():
            text = '<redacted>'
        lines.append(f'{offset:04x} {op} {text}')
    return lines


def trace(apk_path):
    classes, candidates = [], []
    with zipfile.ZipFile(apk_path) as archive:
        for path in sorted(n for n in archive.namelist() if DEX_NAME.fullmatch(n)):
            dex = DEX(archive.read(path))
            for cls in dex.get_classes():
                owner = cls.get_name()
                if owner in TARGETS:
                    section = [f'\nCLASS {owner} extends {cls.get_superclassname()} ({path})']
                    for field in cls.get_fields():
                        section.append(f'FIELD {field.get_access_flags_string()} {field.get_name()} {field.get_descriptor()}')
                    for method in cls.get_methods():
                        name = method.get_name()
                        if owner == 'Lklo;' and name not in {'al', 'aj', 'ap', 'fL', 'fN', 'I', '<init>'}:
                            continue
                        section.append(f'\nMETHOD {owner}->{name}{method.get_descriptor()} {method.get_access_flags_string()}')
                        if method.get_code():
                            section.extend(render(dex, method))
                    classes.append('\n'.join(section))
                else:
                    for method in cls.get_methods():
                        if method.get_code() is None:
                            continue
                        tokens = set()
                        instructions = list(method.get_instructions())
                        for ins in instructions:
                            if ins.get_name() in ('const-string', 'const-string/jumbo'):
                                value = dex.get_cm_string(ins.get_ref_kind()).lower()
                                if value in UI_TOKENS:
                                    tokens.add(value)
                        if tokens:
                            relevant = any(any(t in ins.get_output() for t in ('Lmtr;', 'Lmtm;', 'Lmwv;', 'Lklo;'))
                                           for ins in instructions)
                            header = f'\nMATCH {owner}->{method.get_name()}{method.get_descriptor()} tokens={sorted(tokens)}'
                            if relevant:
                                candidates.append((True, header + '\n' + '\n'.join(render(dex, method))))
                            else:
                                candidates.append((False, header))
            del dex
    candidates.sort(key=lambda x: (not x[0], x[1]))
    return '\n'.join(classes + [value for _, value in candidates[:140]]) + '\n'


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: trace_toolbar.py APK')
    data = gzip.compress(trace(sys.argv[1]).encode('utf-8'), mtime=0)
    encoded = base64.b64encode(data).decode('ascii')
    chunks = [encoded[i:i + 3000] for i in range(0, len(encoded), 3000)]
    if len(chunks) > 60:
        raise SystemExit(f'Trace too large: {len(chunks)} annotation chunks')
    for i, chunk in enumerate(chunks, 1):
        print(f'::notice title=Redacted Gboard toolbar trace {i}/{len(chunks)}::{chunk}')


if __name__ == '__main__':
    main()
