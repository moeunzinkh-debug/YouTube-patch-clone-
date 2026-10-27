"""Record companion APK evidence, without asserting runtime compatibility."""
import hashlib
import json
from pathlib import Path
import sys
from loguru import logger
logger.remove()
from androguard.core.apk import APK

results = []
for filename, expected_package in zip(sys.argv[1:], ['com.google.android.googlequicksearchbox', 'app.revanced.android.gms']):
    path = Path(filename)
    apk = APK(str(path))
    assert apk.get_package() == expected_package, apk.get_package()
    xml = apk.get_android_manifest_xml()
    ns = '{http://schemas.android.com/apk/res/android}'
    permissions = sorted(apk.get_permissions())
    results.append(dict(package=apk.get_package(), version=apk.get_androidversion_name(),
        version_code=apk.get_androidversion_code(), min_sdk=apk.get_min_sdk_version(),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size,
        certificate_sha256=sorted(hashlib.sha256(cert).hexdigest() for cert in apk.get_certificates_der_v2()),
        declared_permissions=sorted(x.get(ns+'name') for x in xml.findall('permission')),
        requested_permissions=permissions,
        provider_authorities=sorted(x.get(ns+'authorities', '') for x in xml.iter('provider')),
        dex_files=sorted(n for n in apk.get_files() if n.endswith('.dex') and '/' not in n),
        split_requirements={k:v for k,v in xml.attrib.items() if 'split' in k.lower()}))
report = {'inspection_only': True, 'runtime_verified': False, 'apks': results,
          'microg_extended_access_declared': 'app.revanced.gms.EXTENDED_ACCESS' in results[1]['declared_permissions']}
Path('docs/gemini-companion-inspection.json').write_text(json.dumps(report, indent=2) + '\n')
for row in results:
    print(row['package'], row['version'], row['version_code'], row['min_sdk'])
