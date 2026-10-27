import json
from pathlib import Path
import sys
from loguru import logger
logger.remove()
from androguard.core.apk import APK

report = json.loads(Path('bundles/gemini/google-patch-result.json').read_text())
assert not report['failedPatches'], report
assert all(step['success'] for step in report['patchingSteps'])
assert len(report['appliedPatches']) >= 8, report
apk = APK(sys.argv[1])
assert apk.get_package() == 'com.google.android.googlequicksearchbox.morphe', apk.get_package()
assert apk.get_androidversion_name() == '17.6.59.ve.arm64'
permissions = apk.get_permissions()
assert 'app.revanced.android.gms.EXTENDED_ACCESS' in permissions
assert 'app.revanced.gms.EXTENDED_ACCESS' not in permissions
xml = apk.get_android_manifest_xml()
ns = '{http://schemas.android.com/apk/res/android}'
assert xml.get(ns+'requiredSplitTypes') is None
meta = {m.get(ns+'name'):m.get(ns+'value') for m in xml.iter('meta-data')}
assert meta['app.revanced.MICROG_PACKAGE_NAME'] == 'app.revanced.android.gms'
result = dict(package=apk.get_package(), version=apk.get_androidversion_name(),
              patch_execution='passed', rebuild='passed', microg_permission='app.revanced.android.gms.EXTENDED_ACCESS',
              device_runtime_tested=False, density_split_still_required_for_complete_resources=True)
Path('bundles/gemini/google-validation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
