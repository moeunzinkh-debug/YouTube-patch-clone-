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
from inspect_account_login import safe_trace_reference

FLOW_SELECTED = {
    'Lf3/a;->h()I',
    'Lf3/a;->e()Landroid/content/Intent;',
    'Lg3/j;->a(Landroid/content/Context;Lcom/google/android/gms/auth/api/signin/GoogleSignInOptions;)Landroid/content/Intent;',
    'Lcom/google/android/gms/auth/api/signin/internal/SignInHubActivity;->onCreate(Landroid/os/Bundle;)V',
}

SELECTED = {
    'Li3/f;->b(Landroid/content/Context;I)I',
    'Li3/k;->c(Landroid/content/pm/PackageInfo;Z)Z',
    # Google Sign-In client mode detection and interactive intent creation:
    # identify whether the checked availability method is actually on-path.
    'Lf3/a;->h()I',
    'Lf3/a;->e()Landroid/content/Intent;',
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


def sanitized_flow(instructions) -> list[dict]:
    """Emit only control flow, register names, small integers and safe references.

    This is limited to four fixed SDK methods. Arbitrary string literals,
    URLs, client IDs and account data are never included in the output.
    """
    offsets = {}
    offset = 0
    for index, ins in enumerate(instructions):
        offsets[offset] = index
        offset += ins.get_length()
    result = []
    offset = 0
    for index, ins in enumerate(instructions):
        opcode = ins.get_name()
        operand = ins.get_output()
        # Registers are emitted as generated labels, never as raw operand text.
        operand_prefix = operand.split('"', 1)[0].split('L', 1)[0]
        registers = re.findall(r'\bv\d{1,3}\b', operand_prefix)
        item = {'index': index, 'opcode': opcode}
        if registers:
            item['registers'] = registers
        if opcode.startswith(('if-', 'goto')) and hasattr(ins, 'get_ref_off'):
            target = offsets.get(offset + 2 * ins.get_ref_off())
            if target is not None:
                item['target_index'] = target
        numeric_operand = None
        if opcode.startswith('const') and not opcode.startswith(('const-string', 'const-class')):
            numeric_operand = re.fullmatch(r'v\d+,\s*(-?(?:0x[\da-f]+|\d+))', operand, re.I)
        elif opcode.endswith(('/lit8', '/lit16')):
            numeric_operand = re.fullmatch(r'v\d+,\s*v\d+,\s*(-?(?:0x[\da-f]+|\d+))', operand, re.I)
        if numeric_operand:
            literal = numeric_operand.group(1)
            number = int(literal, 16 if literal.lstrip('-').lower().startswith('0x') else 10)
            if -16 <= number <= 16:
                item['small_integer'] = number
        if opcode.startswith('const-string'):
            route = extract_route(operand)
            if route:
                item['route'] = route
        elif opcode.startswith(('invoke-', 'sget', 'sput', 'iget', 'iput')):
            reference = safe_trace_reference(operand)
            if reference:
                item['reference'] = reference
        result.append(item)
        offset += ins.get_length()
    return result


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
                        if name in FLOW_SELECTED:
                            found[name]['sanitized_control_flow'] = sanitized_flow(list(method.get_instructions()))
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
