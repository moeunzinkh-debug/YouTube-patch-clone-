#!/usr/bin/env python3
"""Summarize only the pinned SimSimi native navigation/scroll ABI; never publish the APK."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from loguru import logger
from androguard.core.apk import APK
from androguard.core.dex import DEX

logger.remove()
source, output = map(Path, sys.argv[1:3])
expected = 'f18da384232c8e918e1073fd2e95cde6dda9bda2a34f4f90bb527ca95ea8af70'
if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
    raise SystemExit('Unexpected input APK; refusing to inspect')
apk = APK(str(source))
if (apk.get_package(), apk.get_androidversion_name(), apk.get_androidversion_code()) != (
        'com.ismaker.android.simsimi', '9.2.3', '1119001'):
    raise SystemExit('Unexpected SimSimi package/version')

matches = re.compile(r'(?:reactnativenavigation/.{0,100}bottomtabs|bottomnavigation|navigationbar|'
                     r'react/views/scroll/ReactScrollView|/recyclerview/widget/RecyclerView;)', re.I)
classes = []
for dex_bytes in apk.get_all_dex():
    for cls in DEX(dex_bytes).get_classes():
        name = cls.get_name()
        if not matches.search(name):
            continue
        classes.append({
            'name': name,
            'superclass': cls.get_superclassname(),
            'interfaces': cls.get_interfaces(),
            'fields': [{'name': field.get_name(), 'type': field.get_descriptor(),
                        'access': field.get_access_flags_string()} for field in cls.get_fields()],
            'methods': [{'name': method.get_name(), 'descriptor': method.get_descriptor(),
                         'access': method.get_access_flags_string()} for method in cls.get_methods()],
        })
classes.sort(key=lambda item: item['name'])
if not classes or not any('bottom' in cls['name'].lower() for cls in classes):
    raise SystemExit('No expected bottom-navigation classes found')
report = {'package': apk.get_package(), 'version': apk.get_androidversion_name(),
          'source_sha256': expected, 'class_count': len(classes), 'classes': classes,
          'scope': 'Static native class signatures only; no UI/device/runtime proof.'}
output.write_text(json.dumps(report, indent=2) + '\n')
print(f"Found {len(classes)} navigation/scroll classes in the pinned base APK")
