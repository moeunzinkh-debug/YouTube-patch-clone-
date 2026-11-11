#!/usr/bin/env python3
"""Verify actual BigTree MPP outputs at the exact WebView hook; not runtime behavior."""
from __future__ import annotations
import argparse, hashlib, json, re, zipfile
from pathlib import Path

PACKAGE = 'com.app.bigtree'
VERSION = '1.14'
CODE = '10'
BASE_SHA256 = '51b7b05b0171d0f242b37933af8c570dae50b6da3b33a0bfa7dce5814c08977a'
CLASS = 'LG1/m0;'
METHOD = 'onPageFinished'
SELECTORS = {'snap': 'Snap Media', 'translation': 'Translation to English'}
MARKERS = {'snap': 'window.__morpheSnapMedia', 'translation': 'window.__morpheEnglishTranslation'}

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_hook(path: Path) -> list[tuple[str, str]]:
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    logger.remove()
    apk = APK(str(path))
    if (not apk.is_valid_APK() or apk.get_package() != PACKAGE or
            apk.get_androidversion_name() != VERSION or apk.get_androidversion_code() != CODE):
        raise ValueError('Unexpected BigTree APK identity')
    found = []
    dex_names = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not re.fullmatch(r'classes\d*\.dex', name):
                continue
            dex_names.append(name)
            dex = DEX(archive.read(name))
            for cls in dex.get_classes():
                if cls.get_name() != CLASS:
                    continue
                for method in cls.get_methods():
                    if method.get_name() == METHOD and ''.join(method.get_descriptor().split()) == '(Landroid/webkit/WebView;Ljava/lang/String;)V':
                        found.append([(ins.get_name(), ins.get_output()) for ins in method.get_instructions()])
    if len(found) != 1:
        raise ValueError(f'Exact BigTree WebView hook count was {len(found)} across {dex_names}')
    return found[0]

def normalized(instruction: tuple[str, str]) -> tuple[str, str]:
    opcode, output = instruction
    if opcode.startswith('if-') or opcode.startswith('goto'):
        output = ''
    return opcode, re.sub(r'\s+', '', output)

def verify_report(report: Path, output: Path, expected: list[str]) -> None:
    data = json.loads(report.read_text())
    if data.get('packageName') != PACKAGE or data.get('packageVersion') != VERSION:
        raise ValueError('Morphe report has the wrong BigTree identity')
    if data.get('success') is not True or data.get('failedPatches') or data.get('appliedPatches') != expected:
        raise ValueError('Morphe did not apply exactly the requested BigTree selectors')
    steps = data.get('stepResults') or []
    if not {'PATCHING', 'REBUILDING'}.issubset({step.get('step') for step in steps}) or any(step.get('success') is not True for step in steps):
        raise ValueError('Morphe did not report successful patching and rebuilding')
    if Path(data.get('outputPath', '')).resolve() != output.resolve() or not zipfile.is_zipfile(output):
        raise ValueError('Morphe output is absent or does not match the report')

def verify_injection(original: list[tuple[str, str]], patched: list[tuple[str, str]], modes: list[str]) -> None:
    if len(original) != 22 or original[0][0] != 'invoke-super' or original[-1][0] != 'return-void':
        raise ValueError('Reviewed BigTree hook layout changed')
    expected_markers = {MARKERS[mode] for mode in modes}
    for marker in MARKERS.values():
        count = sum(marker in output for _, output in patched)
        if count != (1 if marker in expected_markers else 0):
            raise ValueError('Unexpected injected feature marker count: ' + marker)
    cursor = 1
    installed = set()
    while cursor + 2 < len(patched) and any(marker in patched[cursor][1] for marker in expected_markers):
        first, second, third = patched[cursor:cursor + 3]
        marker = next((value for value in expected_markers if value in first[1]), None)
        if (marker is None or first[0] not in {'const-string', 'const-string/jumbo'} or
                second[0] != 'const/4' or third[0] != 'invoke-virtual' or
                'Landroid/webkit/WebView;->evaluateJavascript(Ljava/lang/String;Landroid/webkit/ValueCallback;)V' not in re.sub(r'\s+', '', third[1])):
            raise ValueError('Injected BigTree JavaScript block has an unexpected shape')
        installed.add(marker)
        cursor += 3
    if installed != expected_markers or len(patched) != len(original) + 3 * len(modes):
        raise ValueError('BigTree injection count or independence check failed')
    stripped = patched[:1] + patched[cursor:]
    if [normalized(x) for x in stripped] != [normalized(x) for x in original]:
        raise ValueError('BigTree patch changed instructions outside the reviewed injection point')

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('base', type=Path)
    parser.add_argument('patched', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('output_report', type=Path)
    parser.add_argument('modes', nargs='+', choices=sorted(SELECTORS))
    args = parser.parse_args()
    if digest(args.base) != BASE_SHA256:
        raise ValueError('Not the exact BigTree pre-release APK')
    expected = [SELECTORS[mode] for mode in args.modes]
    verify_report(args.report, args.patched, expected)
    verify_injection(read_hook(args.base), read_hook(args.patched), args.modes)
    result = {
        'status': 'passed_actual_mpp_application_and_dex_inspection',
        'input_sha256': BASE_SHA256, 'package': PACKAGE, 'version': VERSION, 'version_code': CODE,
        'selectors': expected, 'injection_target': CLASS + '->' + METHOD,
        'injected_markers': [MARKERS[mode] for mode in args.modes],
        'original_hook_preserved_outside_injections': True,
        'runtime_download_translation_network_csp_and_ui_behavior': 'not tested',
    }
    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.write_text(json.dumps(result, indent=2) + '\n')
    print('Verified exact BigTree injection(s):', ', '.join(expected))

if __name__ == '__main__':
    main()
