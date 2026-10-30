#!/usr/bin/env python3
"""Inspect the APK integrity-check call only; never emit literal strings or APK bytes."""
import argparse
import gc
import json
import zipfile
from pathlib import Path

from inspect_apk import DEX_NAME, verify_asset
from trace_translation import method_id, sanitize_focused_instruction

PROTECTOR = 'Lbin/edisaputra/protector/LicenseActivity;'
MAIN = 'Lcom/spaceship/screen/translate/ui/MainActivity;'


def trace(path: Path) -> dict:
    from androguard.core.dex import DEX
    from loguru import logger
    logger.remove()
    verify_asset(path)
    classes = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if not DEX_NAME.fullmatch(info.filename):
                continue
            dex = DEX(archive.read(info))
            for cls in dex.get_classes():
                if cls.get_name() not in (PROTECTOR, MAIN):
                    continue
                methods = []
                for method in cls.get_methods():
                    code = method.get_code()
                    entry = {'method': method_id(cls, method), 'access': method.get_access_flags_string(),
                             'has_code': code is not None}
                    if code is not None and (
                            cls.get_name() == PROTECTOR or method.get_name() == 'onCreate'):
                        instructions = list(method.get_instructions())
                        if cls.get_name() == MAIN:
                            matches = [i for i, inst in enumerate(instructions)
                                       if '->verifyIntegrity(' in inst.get_output()]
                            entry['integrity_windows'] = [
                                {'index': i, 'instructions': [sanitize_focused_instruction(inst)
                                 for inst in instructions[max(0, i-6):i+8]]} for i in matches]
                        else:
                            entry.update({'registers': code.get_registers_size(),
                                          'incoming_registers': code.get_ins_size(),
                                          'instructions': [sanitize_focused_instruction(inst)
                                                           for inst in instructions]})
                    methods.append(entry)
                classes.append({'dex': info.filename, 'class': cls.get_name(), 'super': cls.get_superclassname(),
                                'fields': [{'name': field.get_name(), 'type': field.get_descriptor(),
                                            'access': field.get_access_flags_string()} for field in cls.get_fields()],
                                'methods': methods})
            del dex
            gc.collect()
    if {item['class'] for item in classes} != {PROTECTOR, MAIN}:
        raise ValueError('Expected protector and app activity classes not found')
    return {'scope': 'Pinned input APK; static integrity-call inspection only; string literals redacted',
            'asset_sha256': 'f341a1b174bda7b5d1c95cb2fc84da238228a116844069ee962220acaf1e4e4c',
            'classes': classes}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(trace(args.apk), indent=2) + '\n')
    print('Sanitized integrity-check trace generated')


if __name__ == '__main__':
    main()
