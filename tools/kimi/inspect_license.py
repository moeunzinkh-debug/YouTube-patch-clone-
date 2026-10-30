#!/usr/bin/env python3
"""Inspect PairIP entry points in the pinned Kimi asset; do not execute the APK."""
from __future__ import annotations

import argparse
import gc
import json
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

from inspect_apks import DEX_NAME, SENSITIVE, apk_entries, check_asset

PAIRIP_CLIENT = 'Lcom/pairip/licensecheck/LicenseClient;'
PAIRIP_PROVIDER = 'Lcom/pairip/licensecheck/LicenseContentProvider;'
TARGETS = {
    PAIRIP_CLIENT: {'checkLicense', 'initializeLicenseCheck', 'isLocalCheckPassed',
                    'performLocalInstallerCheck', 'scheduleAppShutdown', 'processResponse'},
    PAIRIP_PROVIDER: {'onCreate'},
}
ENTRYPOINTS = re.compile(r'Lcom/pairip/licensecheck/(?:LicenseClient|LicenseContentProvider);->'
                         r'(?:checkLicense|initializeLicenseCheck|onCreate)\(')
ANDROID = '{http://schemas.android.com/apk/res/android}'


def redact_instruction(op: str, output: str) -> str:
    if op.startswith('const-string') or (output and not output.isprintable()) or len(output) > 500 or SENSITIVE.search(output):
        # Retain no literals from arbitrary application code.
        return '<redacted>'
    return output


def inspect(input_path: Path, apksigner: str) -> dict:
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    logger.remove()
    check_asset(input_path)
    report = {'scope': 'Static inspection; no APK execution or authentication.', 'components': [],
              'pairip_class_names': set(), 'entrypoints': {}, 'entrypoint_callers': []}
    with tempfile.TemporaryDirectory(prefix='kimi-license-') as temp, zipfile.ZipFile(input_path) as outer:
        for n, info in enumerate(apk_entries(outer)):
            path = Path(temp) / f'{n}.apk'
            with outer.open(info) as src, path.open('wb') as dst:
                while chunk := src.read(1024 * 1024):
                    dst.write(chunk)
            apk = APK(str(path))
            split = apk.get_attribute_value('manifest', 'split') or None
            signed = subprocess.run([apksigner, 'verify', '--verbose', '--print-certs',
                                     '--min-sdk-version', '26', str(path)],
                                    capture_output=True, text=True, timeout=120, check=False)
            lines = []
            for line in (signed.stdout + '\n' + signed.stderr).splitlines():
                line = line.replace(str(path), '<component.apk>')
                if (line.startswith(('ERROR:', 'WARNING:', 'DOES NOT VERIFY', 'Verifies', 'Exception'))
                        or re.search(r'(?i)signer|certificate.*digest', line)):
                    lines.append(line[:250])
            component = {'filename': info.filename, 'split': split, 'apksigner_return_code': signed.returncode,
                         'signature_diagnostics': lines[:20]}
            with zipfile.ZipFile(path) as inner:
                names = inner.namelist()
                component['pairip_native_or_vm_assets'] = sorted(name for name in names
                    if re.search(r'(?i)pairip|\.vmcode(?:/|$)', name))[:100]
                component['signature_meta_inf'] = sorted(name for name in names
                    if re.fullmatch(r'META-INF/[^/]+\.(?:RSA|DSA|EC|SF)', name, re.I))[:30]
                if split is None:
                    manifest = apk.get_android_manifest_xml()
                    components = []
                    for node in manifest.xpath('.//provider | .//activity | .//service | .//receiver'):
                        name = node.get(ANDROID + 'name', '')
                        if name.startswith('com.pairip.'):
                            components.append({'type': node.tag, 'name': name,
                                               'enabled': node.get(ANDROID + 'enabled'),
                                               'exported': node.get(ANDROID + 'exported'),
                                               'init_order': node.get(ANDROID + 'initOrder')})
                    component['application_class'] = apk.get_attribute_value('application', 'name')
                    component['pairip_manifest_components'] = components
                    for info_dex in inner.infolist():
                        if not DEX_NAME.fullmatch(info_dex.filename):
                            continue
                        dex = DEX(inner.read(info_dex))
                        for cls in dex.get_classes():
                            cls_name = cls.get_name()
                            if cls_name.startswith('Lcom/pairip/'):
                                report['pairip_class_names'].add(cls_name)
                            for method in cls.get_methods():
                                name = method.get_name()
                                selected = name in TARGETS.get(cls_name, set())
                                if method.get_code() is None:
                                    continue
                                descriptor = ''.join(method.get_descriptor().split())
                                if selected:
                                    method_key = f'{cls_name}->{name}{descriptor}'
                                    code = method.get_code()
                                    record = {'dex': info_dex.filename, 'registers': code.get_registers_size(),
                                              'access_flags': method.get_access_flags_string(), 'instructions': []}
                                matches = []
                                for instruction in method.get_instructions():
                                    op, operand = instruction.get_name(), instruction.get_output()
                                    if selected:
                                        record['instructions'].append({'opcode': op, 'operand': redact_instruction(op, operand)})
                                    if op.startswith('invoke-') and ENTRYPOINTS.search(operand):
                                        matches.append(operand)
                                if selected:
                                    report['entrypoints'][method_key] = record
                                if matches:
                                    report['entrypoint_callers'].append({
                                        'method': f'{cls_name}->{name}{descriptor}',
                                        'calls': sorted(set(matches))})
                        del dex
                        gc.collect()
            report['components'].append(component)
    report['pairip_class_names'] = sorted(report['pairip_class_names'])
    report['entrypoint_callers'].sort(key=lambda entry: entry['method'])
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apks', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--apksigner', required=True)
    args = parser.parse_args()
    result = inspect(args.apks, args.apksigner)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print('PairIP classes:', len(result['pairip_class_names']),
          'entrypoints:', len(result['entrypoints']), 'callers:', len(result['entrypoint_callers']))


if __name__ == '__main__':
    main()
