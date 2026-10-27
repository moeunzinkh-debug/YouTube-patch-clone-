"""Validate the patched artifact statically; does not assert device compatibility."""
import json
from pathlib import Path
import sys
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX

apk = APK(sys.argv[1])
assert apk.get_package() == 'com.google.android.apps.bard'
assert apk.get_androidversion_name() == '1.0.995038376'
assert apk.get_androidversion_code() == '345'
counts = {'original': 0, 'redirected': 0}
for data in apk.get_all_dex():
    for cls in DEX(data).get_classes():
        for method in cls.get_methods():
            if not method.get_code():
                continue
            for ins in method.get_code().get_bc().get_instructions():
                if ins.get_name() in ('const-string', 'const-string/jumbo'):
                    value = ins.get_string()
                    if value == 'com.google.android.googlequicksearchbox':
                        counts['original'] += 1
                    elif value == 'com.google.android.googlequicksearchbox.morphe':
                        counts['redirected'] += 1
assert counts == {'original': 0, 'redirected': 4}, counts
manifest = apk.get_android_manifest_xml()
ns = '{http://schemas.android.com/apk/res/android}'
for attr in ('requiredSplitTypes', 'splitTypes'):
    assert manifest.get(ns + attr) is None and manifest.get(attr) is None
for item in manifest.iter('meta-data'):
    assert item.get(ns + 'name') not in ('com.android.vending.splits.required', 'com.android.vending.splits')
app = manifest.find('application')
assert app.get(ns + 'label') == 'Gemini (Morphe)'
report = {'package': apk.get_package(), 'version': apk.get_androidversion_name(), 'version_code': '345',
          'dex_redirects': counts, 'manifest_checks': 'passed', 'patch_execution': 'passed',
          'device_runtime_tested': False, 'google_microg_new_targets_verified': False}
Path('bundles/gemini/validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
