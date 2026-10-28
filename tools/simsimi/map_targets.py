"""Map exact APK patch targets without modifying entitlements or application code."""
import hashlib
import json
import re
import struct
import sys
import zipfile
from pathlib import Path
from loguru import logger
from androguard.core.apk import APK
from androguard.core.dex import DEX

logger.remove()
source, output = map(Path, sys.argv[1:3])
expected = 'f18da384232c8e918e1073fd2e95cde6dda9bda2a34f4f90bb527ca95ea8af70'
assert hashlib.sha256(source.read_bytes()).hexdigest() == expected, 'Unexpected input APK'
apk = APK(str(source))
android = '{http://schemas.android.com/apk/res/android}'
manifest = apk.get_android_manifest_xml()
report = {'sha256': expected, 'package': apk.get_package(), 'version': apk.get_androidversion_name(),
          'application': apk.get_attribute_value('application', 'name'), 'asset_bundles': [],
          'split_metadata': [], 'app_classes': [], 'entrypoint_disassembly': {},
          'note': 'Static targets only. Features are not implemented by this report.'}
for el in manifest.iter():
    if el.tag == 'uses-split' or el.tag == 'meta-data' and 'split' in el.get(android+'name', '').lower():
        report['split_metadata'].append(dict(el.attrib))
with zipfile.ZipFile(source) as z:
    for name in z.namelist():
        if not name.startswith('assets/') or not name.endswith(('.bundle', '.js', '.hbc')):
            continue
        data = z.read(name)
        item = {'name': name, 'size': len(data), 'header_hex': data[:16].hex(),
                'sha256': hashlib.sha256(data).hexdigest()}
        hermes = data[:8] == bytes.fromhex('c61fbc03c103191f')
        item['format'] = 'hermes' if hermes else 'text-or-other'
        if hermes:
            item['hermes_version'] = struct.unpack_from('<I', data, 8)[0]
        text = data.decode('utf-8', 'replace')
        # Bounded code contexts, never copy complete proprietary bundles into Git.
        terms = ('membership', 'isPremium', 'isVip', 'rewarded', 'interstitial',
                 'RefreshControl', 'onRefresh', 'reload', 'readReceipt', 'subscription')
        item['contexts'] = {}
        for term in terms:
            hits = list(re.finditer(re.escape(term), text, re.I))
            item['contexts'][term] = {'count': len(hits), 'sample': [text[max(0,h.start()-100):h.end()+180] for h in hits[:4]]}
        report['asset_bundles'].append(item)
    for name in z.namelist():
        if not re.fullmatch(r'classes\d*\.dex', name):
            continue
        dex = DEX(z.read(name))
        for cls in dex.get_classes():
            if not cls.get_name().startswith('Lcom/ismaker/android/simsimi/'):
                continue
            report['app_classes'].append({'name': cls.get_name(), 'super': cls.get_superclassname(),
                                          'methods': [m.get_name()+m.get_descriptor() for m in cls.get_methods()]})
            if cls.get_name() not in ('Lcom/ismaker/android/simsimi/MainActivity;', 'Lcom/ismaker/android/simsimi/MainApplication;'):
                continue
            for method in cls.get_methods():
                if method.get_code():
                    report['entrypoint_disassembly'][cls.get_name()+'->'+method.get_name()+method.get_descriptor()] = [
                        ins.get_name()+' '+ins.get_output() for ins in method.get_instructions()][:200]
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
print('Mapped',len(report['app_classes']),'app classes and',len(report['asset_bundles']),'bundles')
