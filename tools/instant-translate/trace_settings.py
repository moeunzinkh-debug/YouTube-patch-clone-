#!/usr/bin/env python3
"""Inspect settings resources and their DEX references without exposing literals or secrets."""
from collections import defaultdict
import argparse
import gc
import json
import re
import zipfile
from pathlib import Path

from inspect_apk import DEX_NAME, EXPECTED_PACKAGE, safe_sample, verify_asset
from trace_translation import method_id, sanitize_focused_instruction

FOCUS = re.compile(r'(?i)(settings?|(?:translation|translate).*(?:engine|model)|(?:engine|model).*(?:translation|translate)|ai_translate)')
EXACT_UI = re.compile(r'(?i)^(settings?|translation settings|translation engine|translate engine|ai translate|model|simple mode styles|vocabulary)$')
FOCUS_NAMES = frozenset({'settings', 'app_settings', 'simple_mode_settings', 'simple_mode_settings_desc', 'hide_settings_button', 'ai_translate'})


def trace(path):
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    from lxml import etree
    logger.remove()
    verify_asset(path)
    apk = APK(str(path))
    if not apk.is_valid_APK() or apk.get_package() != EXPECTED_PACKAGE:
        raise ValueError('Unexpected APK identity')
    resources = apk.get_android_resources()
    entries, anchors = [], {}
    for package in resources.get_packages_names():
        root = etree.fromstring(resources.get_string_resources(package))
        for element in root.iter('string'):
            name = element.get('name', '')
            text = ''.join(element.itertext()).strip()
            if not (FOCUS.search(name) or EXACT_UI.fullmatch(text)) or not safe_sample(name):
                continue
            entry = {'name': name}
            if safe_sample(text): entry['text'] = text
            identifier = resources.get_res_id_by_key(package, 'string', name)
            if isinstance(identifier, int):
                entry['id'] = f'0x{identifier:08x}'
                if EXACT_UI.fullmatch(text) or name in FOCUS_NAMES:
                    anchors[identifier] = name
            entries.append(entry)
    classes, references, bodies, lifecycle = [], defaultdict(list), {}, {}
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if not DEX_NAME.fullmatch(info.filename): continue
            dex = DEX(archive.read(info))
            for cls in dex.get_classes():
                name = cls.get_name()
                if name.startswith('Lcom/spaceship/') and re.search(r'setting', name, re.I):
                    classes.append({'class': name, 'dex': info.filename,
                                    'methods': [method_id(cls, m) for m in cls.get_methods()]})
                for method in cls.get_methods():
                    if method.get_code() is None: continue
                    ins = list(method.get_instructions())
                    if name in {'Lcom/spaceship/screen/translate/SSApplication;',
                                'Lcom/spaceship/screen/translate/ui/MainActivity;'}:
                        code = method.get_code()
                        entry = {'dex': info.filename, 'method': method_id(cls, method),
                                 'registers': code.get_registers_size(), 'incoming_registers': code.get_ins_size()}
                        if method.get_name() in ('onCreate', 'attachBaseContext') and len(ins) <= 3000:
                            entry['instructions'] = [sanitize_focused_instruction(x) for x in ins]
                        lifecycle[entry['method']] = entry
                    for index, inst in enumerate(ins):
                        if not inst.get_name().startswith('const'): continue
                        for literal in inst.get_literals():
                            if literal in anchors and len(references[anchors[literal]]) < 60:
                                references[anchors[literal]].append({
                                    'method': method_id(cls, method), 'dex': info.filename, 'index': index,
                                    'instructions': [sanitize_focused_instruction(x)
                                                     for x in ins[max(0,index-12):index+16]]})
                                if anchors[literal] in {'simple_mode_settings', 'simple_mode_settings_desc'}:
                                    ident = method_id(cls, method)
                                    if len(ins) <= 4000:
                                        code = method.get_code()
                                        bodies[ident] = {'dex': info.filename, 'registers': code.get_registers_size(),
                                            'incoming_registers': code.get_ins_size(),
                                            'instructions': [sanitize_focused_instruction(x) for x in ins]}
            del dex
            gc.collect()
    return {'scope': 'Pinned APK settings metadata only; literal strings and private data redacted',
            'resources': entries, 'anchor_ids': {str(k): v for k,v in anchors.items()},
            'settings_classes': classes, 'anchor_references': dict(references),
            'settings_row_bodies': bodies, 'lifecycle': lifecycle}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(trace(args.apk), indent=2, ensure_ascii=False) + '\n')
    print('Sanitized settings trace generated')


if __name__ == '__main__': main()
