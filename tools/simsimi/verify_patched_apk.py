"""Validate actual Morphe output, not just the transform helper's return value."""
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from loguru import logger
from androguard.core.apk import APK
from androguard.core.dex import DEX
logger.remove()
patched, expected, output = map(Path, sys.argv[1:4])
report = {'engine': 'Morphe Desktop v1.19.1', 'actual_mpp_applied_to_original_apk': True,
          'device_runtime_tested': False, 'full_gms_compatibility_tested': False,
          'server_membership_or_rewards_granted': False,
          'input': 'base only; matching ABI/config splits are required for installation'}
apk = APK(str(patched))
assert 'app.revanced.android.gms.EXTENDED_ACCESS' in apk.get_permissions()
manifest = apk.get_android_manifest_xml()
ns = '{http://schemas.android.com/apk/res/android}'
assert manifest.xpath("./queries/package[@android:name='app.revanced.android.gms']", namespaces={'android': ns[1:-1]})
assert any(e.get(ns+'name') == 'com.android.vending.splits.required' and e.get(ns+'value') == 'true' for e in manifest.iter('meta-data'))
report['microg_permission_and_visibility'] = True
with zipfile.ZipFile(patched) as z:
    actual = z.read('assets/index.android.bundle')
    assert actual == expected.read_bytes(), 'Morphe did not apply both tested Hermes edits'
    report['hermes_payload_matches_tested_transform'] = True
    report['hermes_sha256'] = hashlib.sha256(actual).hexdigest()
    hook_found = runtime_found = False
    routes = 0
    for name in z.namelist():
        if not name.startswith('classes') or not name.endswith('.dex'):
            continue
        dex = DEX(z.read(name))
        for cls in dex.get_classes():
            if cls.get_name() == 'Lapp/morphe/extension/simsimi/PullRefresh;':
                runtime_found = True
            for method in cls.get_methods():
                if not method.get_code():
                    continue
                for instruction in method.get_instructions():
                    text = instruction.get_output()
                    if instruction.get_name().startswith('const-string') and '"app.revanced.android.gms"' in text:
                        routes += 1
                    if cls.get_name() == 'Lcom/ismaker/android/simsimi/MainActivity;' and method.get_name() == 'dispatchTouchEvent':
                        if 'Lapp/morphe/extension/simsimi/PullRefresh;->onTouch(' in text:
                            hook_found = True
    assert hook_found and runtime_found, 'Missing native touch hook or runtime extension'
    assert routes > 0, 'No GMS package literals routed to MicroG RE'
    report.update(injected_main_activity_dispatch_hook=True, injected_pull_refresh_runtime=True, native_microg_routed_literals=routes)
output.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
