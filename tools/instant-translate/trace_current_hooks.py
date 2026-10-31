#!/usr/bin/env python3
"""Read-only focused DEX inspection for the pinned current Instant Translate release."""
import argparse
import gc
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path

from inspect_apk import DEX_NAME, EXPECTED_PACKAGE
from trace_current_release import CODE, VERSION, candidate_owner, method_id, sanitize, verify

PAIRIP = 'Lcom/pairip/'
PAIRIP_FOCUS = frozenset({'Lcom/pairip/application/Application;', 'Lcom/pairip/licensecheck/LicenseClient;',
                          'Lcom/pairip/licensecheck/LicenseContentProvider;'})
REVENUE = ('Lcom/revenuecat/purchases/CustomerInfo;', 'Lcom/revenuecat/purchases/EntitlementInfo;',
           'Lcom/revenuecat/purchases/EntitlementInfos;')
TRANSLATION_SIGS = (r'^\(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;L[^;]+;\)Ljava/lang/Object;$',
                    r'^\(Ljava/util/List;Ljava/lang/String;Ljava/lang/String;L[^;]+;L[^;]+;\)Ljava/lang/Object;$')
GATE_CLASSES = frozenset({'Lf0a;', 'La86;', 'Lu76;', 'Llh8;', 'Lmh8;', 'Lwx0;'})
GATE_METHOD = 'Lf0a;->a(Ljava/lang/String;)Z'


def trace(path):
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    logger.remove()
    verify(path)
    apk = APK(str(path))
    if (not apk.is_valid_APK() or apk.get_package() != EXPECTED_PACKAGE or
            apk.get_androidversion_name() != VERSION or str(apk.get_androidversion_code()) != CODE):
        raise ValueError('Unexpected target identity')
    manifest = apk.get_android_manifest_xml()
    ns = '{http://schemas.android.com/apk/res/android}name'
    manifest_info = {
        'application': [x.get(ns) for x in manifest.iter('application')],
        'pairip_components': [x.get(ns) for x in manifest.iter() if 'pairip' in (x.get(ns) or '').lower()],
        'query_packages': [child.get(ns) for node in manifest.iter('queries') for child in node if child.tag == 'package'],
    }
    entries, fields, callers, entitlements, candidates = {}, {}, defaultdict(list), [], []
    gate_classes, gate_bodies, gate_callers = {}, {}, []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if not DEX_NAME.fullmatch(info.filename): continue
            dex = DEX(archive.read(info))
            for cls in dex.get_classes():
                owner = cls.get_name()
                methods = list(cls.get_methods())
                if owner in PAIRIP_FOCUS:
                    fields[owner] = [{'name': f.get_name(), 'type': ''.join(f.get_descriptor().split()),
                                      'access': f.get_access_flags_string()} for f in cls.get_fields()]
                if owner in GATE_CLASSES:
                    gate_classes[owner] = {'dex': info.filename,
                        'fields': [{'name': f.get_name(), 'type': ''.join(f.get_descriptor().split()),
                                    'access': f.get_access_flags_string()} for f in cls.get_fields()],
                        'methods': [method_id(cls, m) for m in methods]}
                if not candidate_owner(owner) and not owner.startswith(PAIRIP): continue
                for method in methods:
                    code = method.get_code()
                    if code is None: continue
                    identifier = method_id(cls, method)
                    ins = list(method.get_instructions())
                    desc = ''.join(method.get_descriptor().split())
                    if owner in PAIRIP_FOCUS and method.get_name() in {'onCreate', 'attachBaseContext', 'checkLicense', 'initializeLicenseCheck'}:
                        entries[identifier] = {'dex': info.filename, 'access': method.get_access_flags_string(),
                            'registers': code.get_registers_size(), 'incoming': code.get_ins_size(),
                            'instructions': [sanitize(x) for x in ins]}
                    if owner in GATE_CLASSES and len(ins) <= 300:
                        gate_bodies[identifier] = {'dex': info.filename, 'access': method.get_access_flags_string(),
                            'registers': code.get_registers_size(), 'incoming': code.get_ins_size(),
                            'instructions': [sanitize(x) for x in ins]}
                    hits = []
                    for index, inst in enumerate(ins):
                        if not inst.get_name().startswith('invoke-'): continue
                        raw = ''.join(inst.get_output().split())
                        target = raw.rsplit(',', 1)[-1]
                        if 'Lcom/pairip/licensecheck/' in target and any(x in target for x in ('->checkLicense(', '->initializeLicenseCheck(')):
                            if len(callers[target]) < 40: callers[target].append({'method': identifier, 'index': index})
                        if target == GATE_METHOD and len(gate_callers) < 150:
                            gate_callers.append({'method': identifier, 'dex': info.filename, 'index': index,
                                'instructions': [sanitize(x) for x in ins[max(0,index-8):index+10]]})
                        if any(prefix in target for prefix in REVENUE) and any(term in target for term in ('->getEntitlements(', '->getActive(', '->isActive(', '->getAll(')):
                            hits.append({'index': index, 'target': target})
                    if hits and candidate_owner(owner) and len(entitlements) < 120:
                        entitlements.append({'method': identifier, 'dex': info.filename, 'registers': code.get_registers_size(),
                            'access': method.get_access_flags_string(), 'hits': hits,
                            'instructions': [sanitize(x) for x in ins] if len(ins) <= 400 else []})
                    if any(re.fullmatch(p, desc) for p in TRANSLATION_SIGS) and len(candidates) < 150:
                        candidates.append({'method': identifier, 'dex': info.filename, 'registers': code.get_registers_size(),
                            'access': method.get_access_flags_string(),
                            'instructions': [sanitize(x) for x in ins] if len(ins) <= 250 else []})
            del dex
            gc.collect()
    return {'scope': 'Pinned release static metadata and redacted method references only; no app execution or modification',
            'version': VERSION, 'version_code': CODE, 'manifest': manifest_info,
            'pairip_entries': entries, 'pairip_fields': fields, 'pairip_callers': dict(callers),
            'revenuecat_entitlement_callers': entitlements, 'translation_signature_candidates': candidates,
            'gate_classes': gate_classes, 'gate_bodies': gate_bodies, 'gate_callers': gate_callers}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(trace(args.apk), indent=2) + '\n')
    print('Sanitized focused static report generated')


if __name__ == '__main__': main()
