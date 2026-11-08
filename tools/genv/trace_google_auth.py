#!/usr/bin/env python3
"""Trace allowlisted GenV Google-service methods without exposing arbitrary constants."""
from __future__ import annotations
import argparse
import gc
import json
import re
import subprocess
import zipfile
from pathlib import Path
from inspect_genv import DEX_NAME, check_asset
from inspect_google_auth import extract_route, identifier

SELECTED = {
    'Li3/f;->b(Landroid/content/Context;I)I',
    'Li3/k;->c(Landroid/content/pm/PackageInfo;Z)Z',
    'Lg3/j;->a(Landroid/content/Context;Lcom/google/android/gms/auth/api/signin/GoogleSignInOptions;)Landroid/content/Intent;',
    'Lg3/e;->getStartServiceAction()Ljava/lang/String;',
    'Ll3/f;->getStartServicePackage()Ljava/lang/String;',
    'Lcom/google/android/gms/auth/api/signin/internal/SignInHubActivity;->onCreate(Landroid/os/Bundle;)V',
    'Lcom/google/android/gms/auth/api/signin/GoogleSignInOptions;->a(Ljava/lang/String;)Lcom/google/android/gms/auth/api/signin/GoogleSignInOptions;',
    'Lv6/a;->m(Ljava/lang/Object;Lf6/h;)V',
    'Lv6/b;->c(Ljava/lang/String;Ljava/lang/Boolean;Lm6/h;)V',
    'Lv6/b;->d(Lv6/e;)V',
}
ANCHORS = {'MetadataValueReader', 'This should never happen.', 'Google Play Services not available'}


def parse_certificate_digests(text: str) -> list[dict[str, str]]:
    certs = []
    for line in text.splitlines():
        m = re.search(r'certificate SHA-(1|256) digest:\s*([a-fA-F0-9]+)', line, re.I)
        if m and len(m[2]) == (40 if m[1] == '1' else 64):
            prefix = line[:m.start()].strip()
            label = prefix if re.fullmatch(r'[A-Za-z0-9 #=(),.\-:\[\]]{0,120}', prefix) else 'other'
            certs.append({'label': label, 'algorithm': 'sha' + m[1], 'digest': m[2].lower()})
    return certs


def signature_lines(apksigner: str, apk: Path) -> dict:
    result = subprocess.run([apksigner, 'verify', '--verbose', '--print-certs', '--min-sdk-version', '24', str(apk)],
                            check=False, capture_output=True, text=True, timeout=180)
    if result.returncode: raise ValueError('Signature verification failed')
    return {'verified': True, 'public_certificate_digests': parse_certificate_digests(result.stdout + '\n' + result.stderr)}


def trace(apk: Path, apksigner: str) -> dict:
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    from inspect_genv import ANDROID
    logger.remove()
    check_asset(apk)
    manifest_apk = APK(str(apk))
    manifest = manifest_apk.get_android_manifest_xml()
    arsc = manifest_apk.get_android_resources()
    resource_packages = arsc.get_packages_names() if arsc else []
    auth_activities = []
    for activity in manifest.findall('./application/activity'):
        name = activity.get(ANDROID + 'name', '')
        if re.search(r'auth|signin|sign.?in', name, re.I) and identifier(name):
            actions = [a.get(ANDROID + 'name') for a in activity.findall('./intent-filter/action')
                       if a.get(ANDROID + 'name') and extract_route('v0, "' + a.get(ANDROID + 'name') + '"')]
            auth_activities.append({'name': name, 'exported': activity.get(ANDROID + 'exported'), 'gms_actions': actions})
    found = {}
    anchors = {}
    with zipfile.ZipFile(apk) as archive:
        for info in archive.infolist():
            if not DEX_NAME.fullmatch(info.filename): continue
            dex = DEX(archive.read(info))
            for cls in dex.get_classes():
                for method in cls.get_methods():
                    if method.get_code() is None: continue
                    name = cls.get_name() + '->' + method.get_name() + ''.join(method.get_descriptor().split())
                    if not identifier(name): continue
                    is_selected = name in SELECTED
                    ops, references, matched = [], [], set()
                    for idx, ins in enumerate(method.get_instructions()):
                        op = ins.get_name()
                        if is_selected: ops.append(op)
                        if op.startswith('const-string'):
                            operand = ins.get_output()
                            if ',' not in operand: continue
                            value = operand.split(',', 1)[1].strip()
                            if len(value) < 2 or value[0] != '"' or value[-1] != '"': continue
                            value = value[1:-1]
                            if value in ANCHORS: matched.add(value)
                            if is_selected:
                                safe = extract_route(operand)
                                if safe or value in ANCHORS:
                                    references.append({'index': idx, 'opcode': op, 'route_or_anchor': safe or value})
                        elif is_selected and op.startswith(('invoke-', 'sget', 'sput', 'iget', 'iput')):
                            # Method and field identifiers only; never arbitrary operands or string constants.
                            operand = ins.get_output()
                            refs = re.findall(r'L[A-Za-z0-9_$/-]+;->[^,]+', operand)
                            if refs:
                                value = ''.join(refs[-1].split())
                                if identifier(value): references.append({'index': idx, 'opcode': op, 'reference': value})
                    if matched: anchors[name] = sorted(matched)
                    if is_selected:
                        found[name] = {'dex': info.filename, 'flags': method.get_access_flags_string(),
                                       'registers': method.get_code().get_registers_size(),
                                       'instruction_count': len(ops), 'opcodes': ops, 'references': references[:180]}
            del dex
            gc.collect()
    if set(found) != SELECTED: raise ValueError('Selected GenV methods missing: ' + ', '.join(sorted(SELECTED-set(found))))
    check_asset(apk)
    return {'scope': 'Read-only trace; no account access, credentials, URLs, arbitrary strings, execution or APK upload.',
            'signature': signature_lines(apksigner, apk), 'resource_packages': resource_packages,
            'auth_activities': auth_activities, 'selected_methods': found, 'known_anchors': anchors}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk',type=Path); parser.add_argument('output',type=Path); parser.add_argument('--apksigner',required=True)
    args=parser.parse_args(); result=trace(args.apk,args.apksigner)
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('Traced exact auth and availability methods without arbitrary string data.')

if __name__=='__main__': main()
