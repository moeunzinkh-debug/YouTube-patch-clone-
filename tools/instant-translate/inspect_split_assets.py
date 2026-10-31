#!/usr/bin/env python3
"""Inspect supplied split APK metadata and reviewed hook shapes; never patch or execute them."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import re
import zipfile
from pathlib import Path

from inspect_apk import DEX_NAME, EXPECTED_PACKAGE, signature

EXPECTED = {
    'base.apk': (46035628, '8cf8c697d2ce04350d2a7fc7d301751e8bb30cf98f298d288ba8b9bfe3f7b1b2'),
    'split_config.arm64_v8a.apk': (77141662, 'b52f61095730550b1e38c8a3a6bc687261d8eb806ec14012ff765a950bb7d899'),
    'split_config.en.apk': (78034, '8532ec7afd66f4f5bfe53fd357bc7afdec45f2d2eff4ce50f347bb403bd5c84f'),
    'split_config.km.apk': (32978, '4ab8bba827d2d393b5e92bcc5f74bae80da322e970d39118f9c7ed5ea0c11cad'),
    'split_config.xxhdpi.apk': (79279, '4ffa280a432c5848a1db1649ab2528f7ccdbc9d1b50099ff8677e59cf9fb7efd'),
}
TARGETS = {
    'Lbe4;->g0(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Lmx1;)Ljava/lang/Object;': (10, 86),
    'Lkb9;->S(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Lmx1;)Ljava/lang/Object;': (13, 132),
    'Lxm;->D(Ljava/util/List;Ljava/lang/String;Ljava/lang/String;Leh7;Lmx1;)Ljava/lang/Object;': (25, 127),
    'Ldv0;->e(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;': (24, 177),
    'Lcom/spaceship/screen/translate/ui/MainActivity;->onCreate(Landroid/os/Bundle;)V': (13, 129),
    'Lcom/spaceship/screen/translate/SSApplication;->onCreate()V': (5, 96),
}
OWNERS = {target.split('->', 1)[0] for target in TARGETS}
OWNERS.add('Lbin/edisaputra/protector/LicenseActivity;')
OWNERS.update(('Ld29;', 'Lqy8;', 'Lmr0;'))


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(block)
    return sha.hexdigest()


def inspect(directory: Path, signer: str) -> dict:
    from androguard.core.apk import APK
    from androguard.core.dex import DEX
    from loguru import logger
    logger.remove()
    assets, targets, relevant_classes = [], {}, {}
    for name, (size, expected_hash) in EXPECTED.items():
        path = directory / name
        actual = digest(path)
        if path.stat().st_size != size or actual != expected_hash or not zipfile.is_zipfile(path):
            raise ValueError('Supplied split changed or is not an APK: ' + name)
        apk = APK(str(path))
        if not apk.is_valid_APK(): raise ValueError('Invalid APK: ' + name)
        min_sdk = str(apk.get_min_sdk_version() or '29')
        sig = signature(signer, path, min_sdk)
        if not sig['verified']: raise ValueError('Signature verification failed: ' + name)
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)): raise ValueError('Duplicate ZIP entry: ' + name)
            dexes = [x for x in names if DEX_NAME.fullmatch(x)]
            native = [x for x in names if x.startswith('lib/') and x.endswith('.so')]
            for dex_name in dexes:
                data = archive.read(dex_name)
                dex = DEX(data)
                for cls in dex.get_classes():
                    owner = cls.get_name()
                    if owner not in OWNERS: continue
                    fields = sorted((f.get_name(), ''.join(f.get_descriptor().split())) for f in cls.get_fields())
                    relevant_classes[owner] = {'fields': fields, 'dex': dex_name}
                    for method in cls.get_methods():
                        ident = owner + '->' + method.get_name() + ''.join(method.get_descriptor().split())
                        if ident not in TARGETS: continue
                        code = method.get_code()
                        if not code: continue
                        instructions = list(method.get_instructions())
                        entry = {'registers': code.get_registers_size(), 'instructions': len(instructions)}
                        entry['matches_reviewed_shape'] = (entry['registers'], entry['instructions']) == TARGETS[ident]
                        if owner.endswith('/MainActivity;'):
                            entry['integrity_call_present'] = any('->verifyIntegrity(' in i.get_output() for i in instructions)
                        targets[ident] = entry
                del dex
                gc.collect()
            abis = sorted({x.split('/')[1] for x in native if x.count('/') >= 2})
            assets.append({'name': name, 'sha256': actual, 'size': size, 'package': apk.get_package(),
                           'version_name': apk.get_androidversion_name(), 'version_code': apk.get_androidversion_code(),
                           'split': apk.get_attribute_value('manifest', 'split'), 'min_sdk': min_sdk,
                           'signature': sig, 'dex': dexes, 'native_abis': abis, 'native_library_count': len(native)})
    return {'scope': 'Static inventory of newly supplied split APKs; no app execution or modification',
            'expected_package': EXPECTED_PACKAGE, 'assets': assets, 'reviewed_method_shapes': targets,
            'relevant_classes': relevant_classes,
            'all_reviewed_shapes_match': set(targets) == set(TARGETS) and all(x['matches_reviewed_shape'] for x in targets.values()),
            'signers_match': len({tuple(a['signature']['signer_sha256']) for a in assets}) == 1,
            'note': 'Matching method shapes alone never establishes complete compatibility.'}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--apksigner', required=True)
    args = parser.parse_args()
    result = inspect(args.directory, args.apksigner)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Inspected split identities; matching reviewed shapes:', result['all_reviewed_shapes_match'])


if __name__ == '__main__':
    main()
